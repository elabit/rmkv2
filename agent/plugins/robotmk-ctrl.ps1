[CmdletBinding(DefaultParameterSetName = 'Monitor')]
Param(
	[Parameter(ParameterSetName = 'Monitor', Mandatory = $false)]
	[Switch]$Monitor = $($PSCmdlet.ParameterSetName -eq 'Monitor'), # Default action

	[Parameter(ParameterSetName = 'Start', Mandatory = $true)]
	[Switch]$Start, # Start the service

	[Parameter(ParameterSetName = 'Stop', Mandatory = $true)]
	[Switch]$Stop, # Stop the service

	[Parameter(ParameterSetName = 'Restart', Mandatory = $true)]
	[Switch]$Restart, # Restart the service

	[Parameter(ParameterSetName = 'Status', Mandatory = $false)]
	[Switch]$Status, # Get the current service status

	[Parameter(ParameterSetName = 'Setup', Mandatory = $false)]
	[Switch]$Setup,

	[Parameter(ParameterSetName = 'Remove', Mandatory = $true)]
	[Switch]$Remove, # Uninstall the service

	[Parameter(ParameterSetName = 'Service', Mandatory = $true)]
	[Switch]$Service, # Run the service (Internal use only)

	[Parameter(ParameterSetName = 'SCMStart', Mandatory = $true)]
	[Switch]$SCMStart, # Process SCM Start requests (Internal use only)

	[Parameter(ParameterSetName = 'SCMStop', Mandatory = $true)]
	[Switch]$SCMStop, # Process SCM Stop requests (Internal use only)

	[Parameter(ParameterSetName = 'Control', Mandatory = $true)]
	[String]$Control = $null, # Control message to send to the service

	[Parameter(ParameterSetName = 'Version', Mandatory = $true)]
	[Switch]$Version              # Get this script version
)

$argv0 = Get-Item $MyInvocation.MyCommand.Definition
$script = $argv0.basename               # Ex: PSService
$scriptName = $argv0.name               # Ex: PSService.ps1
$scriptFullName = $argv0.fullname       # Ex: C:\Temp\PSService.ps1


#$scriptname = (Get-Item -Path $MyInvocation.MyCommand.Path).PSChildName
# read mode from args or set to 0
$MODE = if ($args[0]) { $args[0] } else { $nul };
$PPID = if ($args[1]) { $args[1] } else { $nul };

$DEBUG = $true
#$DEBUG = $false


$UseRCC = $true

# ==============================================================================
#   __  __          _____ _   _ 
#  |  \/  |   /\   |_   _| \ | |
#  | \  / |  /  \    | | |  \| |
#  | |\/| | / /\ \   | | | . ` |
#  | |  | |/ ____ \ _| |_| |\  |
#  |_|  |_/_/    \_\_____|_| \_|
# ==============================================================================
                              


function main() {
	# robotmk.ps1 : start Robotmk to produce output
	# robotmk-ctrl.ps1 : start Robotmk to control the daemon
	SetScriptVars
	
	Ensure-Directory $RMKlogdir
	Ensure-Directory $RMKTmpDir
	Ensure-Directory $ROBOCORP_HOME
	Ensure-Directory $PDataRobotmk
	LogConfiguration
	
	if ($scriptname -match ".*robotmk.ps1$") {
		RMKOutputProducer
	}
	elseif ($scriptname -match ".*${RMK_ControllerName}$") {
		# (e.g robotmk-controller.ps1)
		# !Was started by the CMK Agent (or on cmdline by user)
		# - Monitor (default action if no arg)
		#   -> Setup (installs/ensures Windows service 'RobotmkAgent')
		#   -> Start
		#      -> Starts Windows Service 'RobotmkAgent'
		#         -> RobotmkAgent.exe (C# stub) - function OnStart() 
		#            (-> RobotmkAgent.ps1 -SCMStart, see below [**])
		# Other commandline actions are: 
		# - Setup
		# - Start
		# - Stop 
		# - Restart
		# - Status
		# - Remove
		# - Foreground
		#   -> run the Robotmk Python Agent, process workload loop in FOREGROUNC
		CLIController
	}
	elseif ($scriptname -match ".*${RMK_AgentName}$") {
		# (e.g. RobotmkAgent.ps1 -SCMStart/-SCMStop)
		# !Was started from Windows SCM via Robotmk.exe, C# stub (see above [**])
		# - SCMStart 
		#   -> Starts RobotmkAgent.ps1 -Service
		#      -> run the Robotmk Python Agent, process workload loop
		# - SCMStop
		#   -> Stops RobotmkAgent.ps1 -Service
		SCMController
	}	
 else {
		LogError "Script name '$scriptname' cannot be evaluated. Exiting."
	}
}

# --------------------------------------------------------------------------
# The 3 main functions

function RMKOutputProducer {
	LogInfo "--- Starting Robotmk Agent Output mode"
	if ($UseRCC) {
		EnsureRCCPresent
		$blueprint = GetCondaBlueprint $RMKCfgDir\conda.yaml		
		if ( IsRCCEnvReady $blueprint ) {
			LogInfo "Robotmk RCC environment is ready to use, Output can be generated"
			RunRobotmkTask "output"
			#$output_str = [string]::Concat($output)
			foreach ($line in $output) {
				Write-Host $line 
			}
		}
		else {
			LogInfo "RCC environment is NOT ready to use. Waiting for Controller to build the environment. Exiting."	
			#TODO: As long as the RCC env is not ready, we should output something interesting
		}
	}
 else {
		# TODO: finalize native python execution
		Write-Host "TODO: finalize native python execution"
	}
}

function CLIController {
	# whenever the CMK Agent calls the plugin, renew the deadman file
	TouchFile $controller_deadman_file	"Controller deadman file"

	# Workaround for PowerShell v2 bug: $PSCmdlet Not yet defined in Param() block
	$Monitor = ($PSCmdlet.ParameterSetName -eq 'Monitor')

	if ($Monitor) {
		# The Checkmk Agent calls the script w/o args. 
		# This mode installs the service and starts it if not already running.
		RMKAgentMonitor
	}

	if ($Status) {
		Write-ServiceStatus
	}

	if ($Setup) {
		RMKAgentSetup
		Write-ServiceStatus
	}

	if ($Start) {
		# the user starts the ps.1 script with -Start
		RMKAgentStart
		Write-ServiceStatus
	}

	if ($Stop) {
		RMKAgentStop
		Write-ServiceStatus
	}

	if ($Restart) {
		RMKAgentRestart
		Write-ServiceStatus
	}

	if ($Remove) {
		RMKAgentRemove
		Write-ServiceStatus
	}
	
	if ($Control) {
		# Send a control message to the service (only for debugging)
		Send-PipeMessage $RMK_AgentPipeName $control
	}
}


function SCMController() {
	
	if ($SCMStart) {
		# Ref 22db44: the SCM calls OnStart() function in the C# stub.
		# This calls the ps1 with arg -SCMStart
		RMKAgentSCMStart
	}	

	if ($SCMStop) {
		# Ref 6e3aaf: the SCM calls OnStop() function in the C# stub. 
		# This calls the ps1 with arg -SCMStop
		RMKAgentSCMStop
	}

	if ($Service) {
		RMKAgentService
	}	
}

# --------------------------------------------------------------------------

#    _____ _      _____ 
#   / ____| |    |_   _|
#  | |    | |      | |  
#  | |    | |      | |  
#  | |____| |____ _| |_ 
#   \_____|______|_____|
                      
# The following functions are called by the CMK Agent or the user. Dispatching by CLIController.

function RMKAgentMonitor {
	# Start-Transcript -Path $null
	$status = RMKAgentStatus
	if ($status -ne "Stopped" -and $status -ne "Running" -and $status -ne "Not Installed") {
		LogWarn "Trying to gracefully stop everything."
		RMKAgentStop
		if ((RMKAgentStatus) -ne "Stopped") {
			LogWarn "Service $RMK_AgentServiceName is still not stopped. Trying to forcefully stop it."
			# TODO: implement forced stop
			RMKAgentStop -Force
			if ((RMKAgentStatus) -ne "Stopped") {
				LogError "Service $RMK_AgentServiceName is still not stopped. Exiting."
				# TODO: Status must be returned to CMK Agent
				return
			}
		}

	}
	if ($status -eq "Stopped" -or $status -eq "Not Installed") {
		LogDebug "Service $RMK_AgentServiceName is $status. "
		RMKAgentSetup
		RMKAgentStart
	}
 elseif ($status -eq "Running") {
		LogDebug "Service $RMK_AgentServiceName is running."
		# - if RCCUse and condahash changed: 
		#    Stop 
		#    Setup
		#    Start	
	}
	$status = RMKAgentStatus
	if ((RMKAgentStatus) -ne "Running") {
		LogError "Service $RMK_AgentServiceName is not running. Exiting."
	}
	#Stop-Transcript
}

function RMKAgentSetup {
	# Install the service
	# Check if it's necessary.
	try {
		$pss = Get-Service $RMK_AgentServiceName -ea stop # Will error-out if not installed
		# If the Controller script is newer than the service script, the service must be removed and reinstalled.
		if ((Get-Item $RMK_AgentFullName -ea SilentlyContinue).LastWriteTime -lt (Get-Item $scriptFullName -ea SilentlyContinue).LastWriteTime) {
			LogDebug "Service $RMK_AgentServiceName is already Installed, but requires upgrade"
			RMKAgentRemove
			throw "continue"
		}
		else {
			LogDebug "Service $RMK_AgentServiceName is already Installed, and up-to-date"
		}
		exit 0
	}
	catch {
		# This is the normal case here. Do not throw or write any error!
		LogDebug "Installation is necessary" # Also avoids a ScriptAnalyzer warning
		# And continue with the installation.
	}
	if (!(Test-Path $PDataRobotmk)) {											 
		New-Item -ItemType directory -Path $PDataRobotmk | Out-Null
	}
	# Copy the service script into the installation directory
	if ($ScriptFullName -ne $RMK_AgentFullName) {
		LogDebug "Installing $ScriptFullName as the Service Executable into $RMK_AgentFullName"
		Copy-Item $ScriptFullName $RMK_AgentFullName
	}
	# Generate the service .EXE from the C# source embedded in this script
	try {
		LogDebug "Compiling C# Service Stub $RMK_AgentExeFullName"
		Add-Type -TypeDefinition $source -Language CSharp -OutputAssembly $RMK_AgentExeFullName -OutputType ConsoleApplication -ReferencedAssemblies "System.ServiceProcess" -Debug:$false
	}
	catch {
		$msg = $_.Exception.Message
		LogError "Failed to create the $RMK_AgentExeFullName service stub. $msg"
		exit 1
	}
	# Register the service
	LogDebug "Registering service $RMK_AgentServiceName (user: LocalSystem)"
	# TODO: Dependency adden!
	$pss = New-Service $RMK_AgentServiceName $RMK_AgentExeFullName -DisplayName $RMK_AgentServiceDisplayName -Description $RMK_AgentServiceDescription -StartupType $RMK_AgentServiceStartupType 
	#$pss = New-Service $RMK_AgentServiceName $RMK_AgentExeFullName -DisplayName $RMK_AgentServiceDisplayName -Description $RMK_AgentServiceDescription -StartupType $RMK_AgentServiceStartupType -DependsOn $RMK_AgentServiceDependsOn
}

function RMKAgentStart {
	# The user tells us to start the service
	LogDebug "Starting service $RMK_AgentServiceName"
	Write-EventLog -LogName $EventLog -Source $RMK_AgentServiceName -EventId 1002 -EntryType Information -Message "$scriptName -Start: Starting service $RMK_AgentServiceName"
	Start-Service $RMK_AgentServiceName # Ask Service Control Manager to start it
}

function RMKAgentStop {
	# Ref 6e3aaf
	# The user tells us to stop the service. 
	LogDebug "Stopping service $RMK_AgentServiceName"
	Write-EventLog -LogName $EventLog -Source $RMK_AgentServiceName -EventId 1004 -EntryType Information -Message "$scriptName -Stop: Stopping service $RMK_AgentServiceName"
	Stop-Service $RMK_AgentServiceName 
	# SCM will now call the OnStop() method of the service, which will call the Agent with -SCMStop
}

function RMKAgentRestart {
	# Restart the service
	RMKAgentStop
	RMKAgentStart
}

function RMKAgentStatus {
	# Get the current service status
	$spid = $null
	# Search for RobotmkAgent.ps1 -Service (this is the process doing the actual service work)
	# See Ref 8b0f1a
	$processes = @(Get-WmiObject Win32_Process -filter "Name = 'powershell.exe'" | Where-Object {
			$_.CommandLine -match ".*$RMK_AgentFullNameEscaped.*-Service"
		})
	foreach ($process in $processes) {
		# There should be just one, but be prepared for surprises.
		$spid = $process.ProcessId
		LogDebug "$RMK_AgentServiceName Process ID = $spid"
	}
	# if (Test-Path "HKLM:\SYSTEM\CurrentControlSet\services\$RMK_AgentServiceName") {}
	try {
		$pss = Get-Service $RMK_AgentServiceName -ea stop # Will error-out if not installed
	}
	catch {
		"Not Installed"
		return
	}
	
	if (($pss.Status -eq "Running") -and (!$spid)) {
		# This happened during the debugging phase
		LogError "Undefined Service state: $RMK_AgentServiceName is started in SCM, but no PID found for '$RMK_AgentServiceName.ps1 -Service'."
		return "noPID"
	}
 else {
		$status = [String]$pss.Status
		#LogInfo "$RMK_AgentServiceName is $status"
		# return status as string
		return $status
	}
}

function RMKAgentRemove {
	# Uninstall the service
	# Check if it's necessary
	# TODO: check if RobotmkAgent.exe is runnning; if so, kill it
	LogDebug "Removing service $RMK_AgentServiceName"
	try {
		$pss = Get-Service $RMK_AgentServiceName -ea stop # Will error-out if not installed
	}
	catch {
		LogDebug "Service ${RMK_AgentServiceName} is already uninstalled"
		return
	}
	Stop-Service $RMK_AgentServiceName # Make sure it's stopped
	# In the absence of a Remove-Service applet, use sc.exe instead.
	
	$msg = sc.exe delete $RMK_AgentServiceName
	if ($LastExitCode) {
		LogError "Failed to remove the service ${serviceName}: $msg"
		exit 1
	}
	else {
		LogDebug $msg
	}
	# Remove the installed files
	if (Test-Path $PDataRobotmk) {
		foreach ($ext in ("exe", "pdb", "ps1")) {
			$file = "$PDataRobotmk\$RMK_AgentServiceName.$ext"
			if (Test-Path $file) {
				LogDebug "Deleting file $file"
				Remove-Item $file
			}
		}
		if (!(@(Get-ChildItem $PDataRobotmk -ea SilentlyContinue)).Count) {
			LogDebug "Removing directory $PDataRobotmk"
			Remove-Item $PDataRobotmk
		}
	}
}


#    _____  _____ __  __ 
#   / ____|/ ____|  \/  |
#  | (___ | |    | \  / |
#   \___ \| |    | |\/| |
#   ____) | |____| |  | |
#  |_____/ \_____|_|  |_|
#
# The following functions are called by the service stub RobotmkAgent.exe     
# Dispatching by SCMController                  
                       
function RMKAgentSCMStart {
	# Ref 22db44: Param -SCMStart
	# The SCM tells us to START the service
	# Do whatever is necessary to start the service script instance
	LogInfo "$scriptFullName -SCMStart: Starting script '$scriptFullName' -Service"
	Write-EventLog -LogName $EventLog -Source $RMK_AgentServiceName -EventId 1001 -EntryType Information -Message "$scriptName -SCMStart: Starting script '$scriptFullName' -Service"
	# Ref 8b0f1a
	# This commandline is searched for in function RMKAgentStatus()
	Start-Process PowerShell.exe -ArgumentList ("-c & '$scriptFullName' -Service")
}

function RMKAgentSCMStop {
	# Ref 6e3aaf: Param -SCMStop
	# The SCM tells us to STOP the service
	# Do whatever is necessary to stop the service script instance
	Write-EventLog -LogName $EventLog -Source $RMK_AgentServiceName -EventId 1003 -EntryType Information -Message "$scriptName -SCMStop: Stopping script $scriptName -Service"
	LogInfo "$scriptName -SCMStop: Stopping script $scriptName -Service"
	# Send an exit message to the service instance
	# Ref 3399b1
	Send-PipeMessage $RMK_AgentPipeName "exit"
}

function RMKAgentService {
	# Ref 8b0f1a: Param -Service
	# RobotmkAgent.ps1 tells us to do the Service work
	Write-EventLog -LogName $EventLog -Source $RMK_AgentServiceName -EventId 1005 -EntryType Information -Message "$scriptName -Service # Beginning background job"
	try {
		# Start the control pipe handler thread
		$pipeThread = Start-PipeHandlerThread $RMK_AgentPipeName -Event "ControlMessage"
		######### TO DO: Implement your own service code here. ##########
		###### Example that wakes up and logs a line every 10 sec: ######
		# Start a periodic timer
		$timerName = "Sample service timer"
		$period = 3 # seconds
		$timer = new-object System.Timers.Timer
		$timer.Interval = ($period * 1000) # Milliseconds
		$timer.AutoReset = $true # Make it fire repeatedly
		Register-ObjectEvent $timer -EventName Elapsed -SourceIdentifier $timerName -MessageData "TimerTick"
		$timer.start() # Must be stopped in the finally block
		# Now enter the main service event loop
		do {
			# Keep running until told to exit by the -Stop handler
			$event = Wait-Event # Wait for the next incoming event
			$source = $event.SourceIdentifier
			$message = $event.MessageData
			$eventTime = $event.TimeGenerated.TimeofDay
			LogDebug "Event at $eventTime from ${source}: $message"
			$event | Remove-Event # Flush the event from the queue
			switch ($message) {
				"ControlMessage" {
					# Required. Message received by the control pipe thread
					$state = $event.SourceEventArgs.InvocationStateInfo.state
					LogDebug "$script -Service # Thread $source state changed to $state"
					switch ($state) {
						"Completed" {
							$message = Receive-PipeHandlerThread $pipeThread
							LogInfo "$scriptName -Service # Received control message: $Message"
							if ($message -ne "exit") {
								# Start another thread waiting for control messages
								$pipeThread = Start-PipeHandlerThread $RMK_AgentPipeName -Event "ControlMessage"
							}
						}
						"Failed" {
							$error = Receive-PipeHandlerThread $pipeThread
							LogInfo "$scriptName -Service # $source thread failed: $error"
							Start-Sleep 1 # Avoid getting too many errors
							$pipeThread = Start-PipeHandlerThread $RMK_AgentPipeName -Event "ControlMessage" # Retry
						}
					}
				}
				"TimerTick" {
					# Example. Periodic event generated for this example
					LogInfo "$scriptName -Service # Timer ticked"
				}
				default {
					# Should not happen
					LogInfo "$scriptName -Service # Unexpected event from ${source}: $Message"
				}
			}
			# Ref 3399b1
		} while ($message -ne "exit")
	}
	catch {
		# An exception occurred while runnning the service
		$msg = $_.Exception.Message
		$line = $_.InvocationInfo.ScriptLineNumber
		LogInfo "$scriptName -Service # Error at line ${line}: $msg"
	}
	finally {
		# Invoked in all cases: Exception or normally by -Stop
		# Cleanup the periodic timer used in the above example
		Unregister-Event -SourceIdentifier $timerName
		$timer.stop()
		############### End of the service code example. ################
		# Terminate the control pipe handler thread
		Get-PSThread | Remove-PSThread # Remove all remaining threads
		# Flush all leftover events (There may be some that arrived after we exited the while event loop, but before we unregistered the events)
		$events = Get-Event | Remove-Event
		# Log a termination event, no matter what the cause is.
		Write-EventLog -LogName $EventLog -Source $RMK_AgentServiceName -EventId 1006 -EntryType Information -Message "$script -Service # Exiting"
		LogInfo "$scriptName -Service # Exiting"
	}
	return


	# HEREIWAS 2 
	# # Das gehört in RMKAGentService 
	# # use RCC? 
	# # yes:
	# # - check if RCC env is ready 
	# # - check if Agent runs 
	# # no: 
	# # - check if native python env is ready
	# # Starts the Robotmk process with RCC or native Python
	# # TODO: How to make RCC execution an optional feature?

	# Start-Sleep -Seconds 20000
	# Start-Sleep -Seconds 20000
	# if ($UseRCC) {
	# 	EnsureRCCPresent
	# 	$blueprint = GetCondaBlueprint $RMKCfgDir\conda.yaml			
		
	# 	if ( IsRCCEnvReady $blueprint) {
	# 		# if the RCC environment is ready, start the Agent if not yet running
	# 		LogInfo "Robotmk RCC environment is ready to use."
	# 		if (IsRobotmkAgentRunning) {
	# 			LogInfo "Nothing to do, Robotmk Agent is already running."
	# 		}
	# 		else {
	# 			RunRobotmkTask "agent"
	# 		}			
	# 	}		
	# 	else {	
	# 		# otherwise, try to create the environment	
	# 		if (IsFlagfileYoungerThanMinutes $Flagfile_RCC_env_creation_in_progress $RCC_env_max_creation_minutes) {
	# 			LogWarn "Robotmk RCC environment is NOT ready to use."
	# 			LogWarn "Another Robotmk RCC environment creation is in progress (flagfile $Flagfile_RCC_env_creation_in_progress present and younger than $RCC_env_max_creation_minutes min). Exiting."
	# 			return
	# 		}
	# 		else {
	# 			LogWarn "RCC environment is NOT ready to use."
	# 			LogWarn "Will now try to create a new RCC environment."
	# 			RemoveFlagfile $Flagfile_RCC_env_robotmk_ready
	# 			TouchFile $Flagfile_RCC_env_creation_in_progress "RCC creation state file"
	# 			if (Test-Path ($RMKCfgDir + "\hololib.zip")) {
	# 				LogInfo "hololib.zip found in $RMKCfgDir, importing it"
	# 				RCCImportHololib "$RMKCfgDir\hololib.zip"
	# 				# TODO: create spaces for agent /output?
	# 			}
	# 			else {
	# 				LogInfo "Catalog must be created from network (hololib.zip not found in $RMKCfgDir)"		
	# 				# Create a separate Holotree Space for agent and output	
	# 				RCCEnvironmentCreate "$RMKCfgDir\robot.yaml" $rcc_ctrl_rmk $rcc_space_rmk_agent
	# 				RCCEnvironmentCreate "$RMKCfgDir\robot.yaml" $rcc_ctrl_rmk $rcc_space_rmk_output
	# 			}
	# 			# This takes some minutes... 
	# 			# Watch the progress with `rcc ht list` and `rcc ht catalogs`. First the catalog is created, then
	# 			# both spaces.
	# 			if (CatalogContainsAgentBlueprint $blueprint) {
	# 				TouchFile $Flagfile_RCC_env_robotmk_ready "RCC env ready flagfile"
	# 				RemoveFlagfile $Flagfile_RCC_env_creation_in_progress	
	# 				LogInfo "OK: Environments for Robotmk created and ready to use on next run. Exiting now."		
	# 			}
	# 			else {
	# 				LogInfo "RCC environment creation for Robotmk agent failed for some reason. Exiting."
	# 				RemoveFlagfile $Flagfile_RCC_env_creation_in_progress
	# 			}
	# 		}

	# 	}		
		
	# }
	# else {
	# 	# TODO: finalize native python execution
	# 	$Binary = $PythonExe
	# 	$Arguments = "$PythonExe $RobotmkAgent"
	# }
	


	
	# HEREIWAS	
	# 	if (IsRobotmkAgentServiceRunning) {
	# 		# get md5 hash of conda.yaml
	# 		$conda_hash = GetFileHash $RMKCfgDir\conda.yaml
	# 		if ($conda_hash -eq $null) {
	# 			LogError "Cannot get hash of conda.yaml. Exiting."
	# 			return
	# 		}
	# 		# check if hash is in cache file
	# 		if (Test-Path $conda_yml_hashfile) {
	# 			$hash_cached = Get-Content $conda_yml_hashfile
	# 			if ($hash_cached -eq $conda_hash) {
	# 				LogDebug "conda.yaml hash is unchanged, nothing to do."
	# 				return
	# 			}
	# 			else {
	# 				LogInfo "conda.yaml hash has changed, restarting Robotmk Agent service."
	# 				RestartRobotmkAgentService
	# 				Set-Content $conda_yml_hashfile $conda_hash
	# 			}
	# 		}
	# 		else {
	# 			LogInfo "conda.yaml hash is not cached, restarting Robotmk Agent service."
	# 			RestartRobotmkAgentService
	# 			Set-Content $conda_yml_hashfile $conda_hash
	# 		}
	# 	}
	#  else {
	# 		LogInfo "Service '$RMK_AgentServiceName' is not running."
	# 		StartRobotmkAgentService
	# 	}

}


function Invoke-Process {
	<#
	.GUID b787dc5d-8d11-45e9-aeef-5cf3a1f690de
	.AUTHOR Adam Bertram
	.COMPANYNAME Adam the Automator, LLC
	.TAGS Processes
	#>	
	[CmdletBinding(SupportsShouldProcess)]
	param
	(
		[Parameter(Mandatory)]
		[ValidateNotNullOrEmpty()]
		[string]$FilePath,

		[Parameter()]
		[ValidateNotNullOrEmpty()]
		[string]$ArgumentList
	)

	$ErrorActionPreference = 'Stop'

	try {
		$stdOutTempFile = "$env:TEMP\$((New-Guid).Guid)"
		$stdErrTempFile = "$env:TEMP\$((New-Guid).Guid)"

		$startProcessParams = @{
			FilePath               = $FilePath
			ArgumentList           = $ArgumentList
			RedirectStandardError  = $stdErrTempFile
			RedirectStandardOutput = $stdOutTempFile
			Wait                   = $true;
			PassThru               = $true;
			NoNewWindow            = $true;
		}
		if ($PSCmdlet.ShouldProcess("Process [$($FilePath)]", "Run with args: [$($ArgumentList)]")) {
			$cmd = Start-Process @startProcessParams
			$cmdOutput = Get-Content -Path $stdOutTempFile -Raw
			$cmdError = Get-Content -Path $stdErrTempFile -Raw
			return @{
				ExitCode = $cmd.ExitCode
				Stdout   = $cmdOutput
				Stderr   = $cmdError
				Output   = $cmdOutput + $cmdError
			}
		}
	}
	catch {
		$PSCmdlet.ThrowTerminatingError($_)
	}
	finally {
		Remove-Item -Path $stdOutTempFile, $stdErrTempFile -Force -ErrorAction Ignore
	}
}




function IsRobotmkAgentServiceRunning {
	# Check if Service is running
	$service = Get-Service -Name $RMK_AgentServiceName -ErrorAction SilentlyContinue
	if ($service -eq $null) {
		#LogInfo "Service $RMK_AgentServiceName not installed."
		return $false
	}
	else {
		if ($service.Status -eq "Running") {
			#LogDebug "Service $RMK_AgentServiceName running."
			return $true
		}
		else {
			#LogInfo "Service $RMK_AgentServiceName not running."
			return $false
		}
	}
}

function StartRobotmkAgentService {
	# Check if Service is running
	$service = Get-Service -Name $RMK_AgentServiceName -ErrorAction SilentlyContinue
	if ($service -eq $null) {
		LogInfo "Service $RMK_AgentServiceName not installed."
		return $false
	}
	else {
		if ($service.Status -eq "Running") {
			LogDebug "Service $RMK_AgentServiceName already running."
			return $true
		}
		else {
			LogInfo "Starting service $RMK_AgentServiceName."
			Start-Service -Name $RMK_AgentServiceName -ErrorAction SilentlyContinue
			return $true
		}
	}
}


function IsRobotmkAgentRunning {
	# TODO: can only see own processes! 
	$processes = GetProcesses -Cmdline "%robotmk.exe agent bg"
	# if length of array is 0, no process is running
	if ($processes.Length -eq 0) {
		if (Test-Path $agent_pidfile) {
			LogInfo "No process 'robotmk.exe agent bg' is running, removing stale PID file $agent_pidfile."
			Remove-Item $agent_pidfile -Force -ErrorAction SilentlyContinue
		}
		else {
			LogDebug "No process 'robotmk.exe agent bg' is running."
		}
		return $false
	}	
	else {
		# --- Facade plugin only watches if there is a process running with the PID 
		# from the pidfile.
		# --- agent.py will create a new pidfile for its own process.
		# Ref: 5ea7ddc (agent.py)
		# Read PID from pidfile and check if THIS is still running
		# - PID from file is found: OK, go out 
		# - PID from file not found: delete deadman file (forces the to also exit)
		if (Test-path $agent_pidfile) {
			$pidfromfile = Get-Content $agent_pidfile
			# if pidfromfile is in the list of running processes, we are good
			if ($processes -contains $pidfromfile) {
				LogDebug "The PID $pidfromfile is already running and in pidfile $agent_pidfile."
				return $true
			}
			else {
				LogError "The PID read from $agent_pidfile ($pidfromfile) des NOT seem to run."
				# option 1: kill all processes (favoured)
				LogWarn "Killing all processes matching the pattern '*robotmk*agent*(fg/bg)': $processes"				
				$processes | ForEach-Object {
					Stop-Process -Id $_ -Force				
				}				
				# option 2: only remove the deadman file (agent.py will exit; use this only if killing os not an option)
				#Remove-Item $controller_deadman_file -Force -ErrorAction SilentlyContinue
				return $false
			}
		}
		else {
			LogWarn "Processes matching the pattern '*robotmk*agent*(fg/bg)' are running ($processes), but NO PID file found for."
			LogWarn "Waiting for agent to create a PID file ($file) itself."
		}				
	}

}


#   _____   _____ _____   _          _                 
#  |  __ \ / ____/ ____| | |        | |                
#  | |__) | |   | |      | |__   ___| |_ __   ___ _ __ 
#  |  _  /| |   | |      | '_ \ / _ \ | '_ \ / _ \ '__|
#  | | \ \| |___| |____  | | | |  __/ | |_) |  __/ |   
#  |_|  \_\\_____\_____| |_| |_|\___|_| .__/ \___|_|   
#                                     | |              
#                                     |_|              


function IsRCCEnvReady {
	# This approach checks if the blueprint is really in the catalog list. 
	param (
		[Parameter(Mandatory = $True)]
		[string]$blueprint
	)

	if ((CatalogContainsAgentBlueprint $blueprint) -and (HolotreeContainsAgentSpaces $blueprint)) {
		if (IsFlagfilePresent $Flagfile_RCC_env_robotmk_ready) {
			return $true
		}
		else {
			TouchFile $Flagfile_RCC_env_robotmk_ready	 "RCC env ready flagfile"		
			return $true
		}
	}
	else {
		RemoveFlagfile $Flagfile_RCC_env_robotmk_ready
		return $false
	}	
}

function GetCondaBlueprint {
	# Get the blueprint hash for conda.yaml
	param (
		[Parameter(Mandatory = $True)]
		[string]$conda_yaml
	)	
	LogDebug "!!  rcc ht hash $conda_yaml"
	$ret = Invoke-Process -FilePath $RCCExe -ArgumentList "ht hash $conda_yaml"
	$out = $ret.Output
	LogDebug $out
	#$condahash = & $RCCExe ht hash $conda_yaml 2>&1
	$m = $out -match "Blueprint hash for.*is (?<blueprint>[A-Za-z0-9]*)\."
	$blueprint = $Matches.blueprint
	return $blueprint
}

function CatalogContainsAgentBlueprint {
	param (
		[Parameter(Mandatory = $True)]
		[string]$blueprint
	)
	LogDebug "Checking if blueprint $blueprint is in RCC catalog..."
	LogDebug "!!  rcc ht catalogs"
	$ret = Invoke-Process -FilePath $RCCExe -ArgumentList "ht catalogs"
	$rcc_catalogs = $ret.Output
	#	$rcc_catalogs = & $RCCExe ht catalogs 2>&1
	#$catalogstring = [string]::Concat($rcc_catalogs)
	$catalogstring = $rcc_catalogs -join "\n"
	LogDebug "Catalogs:\n $rcc_catalogs"
	if ($catalogstring -match "$blueprint") {
		LogDebug "OK: Blueprint $blueprint is in RCC catalog."
		return $true
	}
	else {
		LogWarn "Blueprint $blueprint is NOT in RCC catalog."
		return $false
	}
}

function HolotreeContainsAgentSpaces {
	# Checks if the RCC holotree spaces contain BOTH a line for AGENT and OUTPUT space
	param (		
		[Parameter(Mandatory = $True)]
		[string]$blueprint
	)  	
	# Example: rcc.robotmk  output  c939e5d2d8b335f9
	LogDebug "Checking if holotree spaces contain both, a line for AGENT and OUTPUT space..."
	LogDebug "!!  rcc ht list"
	$ret = Invoke-Process -FilePath $RCCExe -ArgumentList "ht list"
	$holotree_spaces = $ret.Output
	$spaces_string = $holotree_spaces -join "\n"
	LogDebug "Holotree spaces: \n$spaces_string"
	# AGENT SPACE
	$agent_match = ($spaces_string -match "rcc.$rcc_ctrl_rmk\s+$rcc_space_rmk_agent\s+$blueprint")
	if (-Not ($agent_match)) {
		LogWarn "Conda hash '$blueprint' not found for holotree space 'rcc.$rcc_ctrl_rmk/$rcc_space_rmk_agent'."
	}
	else {
		LogDebug "OK: Conda hash '$blueprint' found for holotree space 'rcc.$rcc_ctrl_rmk/$rcc_space_rmk_agent'."
	}	
	# OUTPUT SPACE
	$output_match = ($spaces_string -match "rcc.$rcc_ctrl_rmk\s+$rcc_space_rmk_output\s+$blueprint")
	if (-Not ($output_match)) {
		LogWarn "Conda hash '$blueprint' not found for holotree space 'rcc.$rcc_ctrl_rmk/$rcc_space_rmk_output'."
	}
	else {
		LogDebug "OK: Conda hash '$blueprint' found for holotree space 'rcc.$rcc_ctrl_rmk/$rcc_space_rmk_output'."
	}
	
	if ($agent_match -and $output_match) {
		return $true
	}
	else {
		return $false
	}
}


function RCCEnvironmentCreate {
	# Creates/Ensures an environment with controller (app) and space (mode)
	param (
		[Parameter(Mandatory = $True)]
		[string]$robot_yml,
		[Parameter(Mandatory = $True)]
		[string]$controller,
		[Parameter(Mandatory = $True)]
		[string]$space				
	)  
	LogInfo "Creating Holotree space '$controller/$space' for Robotmk agent."
	$Arguments = "holotree vars --controller $controller --space $space -r $robot_yml"
	LogInfo "!!  $RCCExe $Arguments"
	$ret = Invoke-Process -FilePath $RCCExe -ArgumentList $Arguments
	$rc = $ret.ExitCode
	LogDebug $ret.Output
	if ($rc -eq 0) {
		LogInfo "RCC environment creation for Robotmk agent successful."
	}
	else {
		LogError "RCC environment creation for Robotmk agent FAILED for some reason."
	}
	
}

function RCCImportHololib {
	# Runs a RCC task
	param (
		[Parameter(Mandatory = $True)]
		[string]$hololib_zip
	)  
	$Arguments = "holotree import $hololib_zip"
	$p = Start-Process -Wait -FilePath $RCCExe -ArgumentList $Arguments
	$p.StandardOutput
	$p.StandardError
}



function EnsureRCCPresent {
	# Check if the RCCExe binary is present. If not, download it.
	if (Test-Path $RCCExe) {
		LogDebug "RCC.exe found at $RCCExe."
	}
	else {
		LogInfo "RCCExe $RCCExe not found, downloading it."
		$RCCExeUrl = "https://downloads.robocorp.com/rcc/releases/v11.30.0/windows64/rcc.exe"
		[Net.ServicePointManager]::SecurityProtocol = "tls12, tls11, tls"
		Invoke-WebRequest -Uri $RCCExeUrl -OutFile $RCCExe
	}
}


function RunRobotmkTask {
	param (
		[Parameter(Mandatory = $True)]
		[string]$rmkmode
	)	
	$rcctask = "robotmk-$rmkmode"
	#RCCTaskRun "robotmk-agent" "$RMKCfgDir\robot.yaml" $rcc_ctrl_rmk $rcc_space_rmk_agent
	$space = (Get-Variable -Name "rcc_space_rmk_$rmkmode").Value
	LogDebug "Running Robotmk task '$rcctask' in Holotree space '$rcc_ctrl_rmk/$space'"
	$Arguments = "task run --controller $rcc_ctrl_rmk --space $space -t $rcctask -r $RMKCfgDir\robot.yaml"
	LogDebug "!!  $RCCExe $Arguments"
	# As the script waits "forever", there is no PID known here. Next execution of 
	# the controller will create it. 
	$ret = Invoke-Process -FilePath $RCCExe -ArgumentList $Arguments
	# -------------------------------------
	# --- ROBOTMK AGENT IS RUNNING HERE ---
	# ------------- DAEMONIZED ------------
	# -------------------------------------
	# We should not come here!
	
	$rc = $ret.ExitCode
	# Read last exit code from file (RCC cannot return the exit code of the task. )
	$robotmk_agent_lastexitcode = GetAgentLastExitCode

	LogInfo "Robotmk task '$rcctask' terminated."
	LogInfo "Last Message was: '$robotmk_agent_lastexitcode'" 
}



#   _          _                 
#  | |        | |                
#  | |__   ___| |_ __   ___ _ __ 
#  | '_ \ / _ \ | '_ \ / _ \ '__|
#  | | | |  __/ | |_) |  __/ |   
#  |_| |_|\___|_| .__/ \___|_|   
#               | |              
#               |_|              

function GetAgentLastExitCode {
	# Returns from file the last exit code of the Robotmk Agent
	if (Test-Path $robotmk_agent_lastexitcode) {
		$content = Get-Content $robotmk_agent_lastexitcode
	}
	else {
		$content = "- Robotmk Agent did not write any exit code (file does not exist)"
	}
	return $content
}


function TouchFile {
	param (
		[Parameter(Mandatory = $True)]
		[string]$path,
		[Parameter(Mandatory = $False)]
		[string]$name = "file"
	)  
	LogDebug "Touching $name $path"
	$nul > $path
}

function RemoveFlagfile {
	param (
		[Parameter(Mandatory = $True)]
		[string]$path = $null
	)  
	LogDebug "Removing flagfile $path"
	Remove-Item ($path) -Force -ErrorAction SilentlyContinue
}


function IsFlagfilePresent {
	param (
		[Parameter(Mandatory = $True)]
		[string]$flagfile
	)  	
	if (Test-Path $flagfile) {
		LogInfo "Flagfile $flagfile found"
		return $true
	}
	else {
		return $false
	}
}


# function to reads file's timestamp and return true if file is younger than 60 seconds
function IsFlagfileYoungerThanMinutes {
	param (
		[Parameter(Mandatory = $True)]
		[string]$path,
		[Parameter(Mandatory = $True)]
		[int]$minutes
	)  
	# exit if file does not exist
	if (Test-Path $path) {
		$now = Get-Date
		$lastexec = Get-Date (Get-Item $path).LastWriteTime
		$diff = $now - $lastexec
		if (($diff.TotalSeconds / 60) -lt $minutes) {
			return $true
		}
		else {
			return $false
		}
	}
	else {
		return $false
	}
}

function GetProcesses {
	param (
		[Parameter(Mandatory = $True)]
		[string]$Cmdline
	)
	# TODO: unsauber!
	#LogInfo '!! Get-WmiObject -Query "SELECT * FROM Win32_Process WHERE CommandLine like "'$Cmdline'" | Select ProcessId'
	#Get-WmiObject -Query "SELECT * FROM Win32_Process" | Export-Csv -Path c:\all.csv -NoTypeInformation -Encoding ASCII
	$processId = Get-WmiObject -Query "SELECT * FROM Win32_Process WHERE CommandLine like '$Cmdline'" | Select ProcessId
	
	#LogInfo "ProcessId: $processId"
	return $processId.processId

}

function Ensure-Directory {
	param (
		[Parameter(Mandatory = $True)]
		[string]$directory
	)
	if (-Not (Test-Path $directory)) {
		#LogInfo "Directory $directory does not exist, creating it."
		New-Item -ItemType Directory -Path $directory -Force -ErrorAction SilentlyContinue | Out-Null
	}
}

function Get-EnvVar {
	# return environment variable or default value
	param (
		[Parameter(Mandatory = $True)]
		[string]$name, 
		[Parameter(Mandatory = $True)]
		[string]$default = ""
	)
	$value = [System.Environment]::GetEnvironmentVariable($name)
	if ($value -eq $null) {
		return $default
	}
	else {
		return $value
	}
}

function Set-EnvVar {
	param (
		[Parameter(Mandatory = $True)]
		[string]$name,
		[Parameter(Mandatory = $True)]
		[string]$value
	)
	[System.Environment]::SetEnvironmentVariable($name, $value)
} 

function Get-CurrentUserName {
	# Identify the user name. We use that for logging.
	$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
	$currentUserName = $identity.Name # Ex: "NT AUTHORITY\SYSTEM" or "Domain\Administrator"
	return $currentUserName
}


Function Now {
	Param (
		[Switch]$ms, # Append milliseconds
		[Switch]$ns         # Append nanoseconds
	)
	$Date = Get-Date
	$now = ""
	$now += "{0:0000}-{1:00}-{2:00} " -f $Date.Year, $Date.Month, $Date.Day
	$now += "{0:00}:{1:00}:{2:00}" -f $Date.Hour, $Date.Minute, $Date.Second
	$nsSuffix = ""
	if ($ns) {
		if ("$($Date.TimeOfDay)" -match "\.\d\d\d\d\d\d") {
			$now += $matches[0]
			$ms = $false
		}
		else {
			$ms = $true
			$nsSuffix = "000"
		}
	} 
	if ($ms) {
		$now += ".{0:000}$nsSuffix" -f $Date.MilliSecond
	}
	return $now
}


function SetScriptVars {
	# TODO: Set RObocorp Home with robotmk.yaml
	# Programdata var
	$PData = [System.Environment]::GetFolderPath("CommonApplicationData")
	$Global:PDataCMK = "$PData\checkmk"
	$Global:PDataCMKAgent = "$PDataCMK\agent"
	# Set to tmp dir for testing
	$Global:PDataRobotmk = "$PDataCMK\robotmk"
	#$Global:PDataRobotmk = "${PData}\robotmk\plugins"

	# The name of the Checkmk Agent Plugin
	$Global:RMK_Controller = "robotmk-ctrl"
	$Global:RMK_ControllerName = "${RMK_Controller}.ps1"

	# Windows Service vars
	# RMKA = Robotmk Agent
	$Global:RMK_AgentServiceName = "RobotmkAgent"
	$Global:RMK_AgentServiceDisplayName = $RMK_AgentServiceName
	$Global:RMK_AgentServiceDescription = "Robotmk Agent for Robot Framework execution and monitoring"
	$Global:RMK_AgentServiceStartupType = "Manual"
	$Global:RMK_AgentServiceDependsOn = @("CheckmkService")	

	# Windows service executable vars
	$Global:RMK_Agent = $RMK_AgentServiceName
	$Global:RMK_AgentName = "${RMK_Agent}.ps1"
	$Global:RMK_AgentFullName = "$PDataRobotmk\${RMK_AgentName}"
	$Global:RMK_AgentFullNameEscaped = $RMK_AgentFullName -replace "\\", "\\" 

	# Where to install the service files
	$Global:RMK_AgentExeName = "$RMK_AgentServiceName.exe"
	$Global:RMK_AgentExeFullName = "$PDataRobotmk\$RMK_AgentExeName"	
	$Global:RMK_AgentPipeName = "Service_$RMK_AgentServiceName" 

	# Try to read the environment variables from the agent. If not set, use defaults.
	$Global:MK_LOGDIR = "$PDataCMKAgent\log"
	$Global:RMKLogDir = "$MK_LOGDIR\robotmk"
	$Global:MK_TEMPDIR = "$PDataCMKAgent\tmp"
	$Global:RMKTmpDir = "$MK_TEMPDIR\robotmk"
	$Global:MK_CONFDIR = "$PDataCMKAgent\config"
	$Global:RMKCfgDir = "$MK_CONFDIR\robotmk"
	$Global:RMKLogfile = "$RMKLogDir\${script}.log"	

	$Global:EventLog = "Application"    
	$Global:ROBOCORP_HOME = if ($env:ROBOCORP_HOME) { $env:ROBOCORP_HOME } else { 
		# use user tmp dir if not set
		$env:TEMP + "\ROBOCORP"
	};
	Set-EnvVar "ROBOCORP_HOME" $ROBOCORP_HOME	

	# Expose env vars for CMK agent (they exist if called from agent, but 
	# do NOT if called while developing)
	Set-EnvVar "ROBOTMK_LOGDIR" $RMKLogDir 
	Set-EnvVar "ROBOTMK_TMPDIR" $RMKTmpDir 
	Set-EnvVar "ROBOTMK_CFGDIR" $RMKCfgDir

	# FILES ========================================

	# TODO: Deploy with Bakery
	$Global:RCCExe = $PDataCMKAgent + "\bin\rcc.exe"
	# Ref 7e8b2c1 (agent.py)
	$Global:agent_pidfile = $RMKTmpDir + "\robotmk_agent.pid"

	$Global:conda_yml_hashfile = $RMKTmpDir + "\robotmk_conda_yml_hash.txt"
	# Ref 23ff2d1 (agent.py)
	$Global:controller_deadman_file = $RMKTmpDir + "\robotmk_controller_deadman_file"
	# This flagfile indicates that both there is a usable holotree space for "robotmk agent/output"
	$Global:Flagfile_RCC_env_robotmk_ready = $RMKTmpDir + "\rcc_env_robotmk_agent_ready"
	$Global:robotmk_agent_lastexitcode = $RMKTmpDir + "\robotmk_agent_lastexitcode"
	# IMPORTANT! All other Robot subprocesses must respect this file and not start if it is present!
	# (There is only ONE RCC creation allowed at a time.)
	$Global:Flagfile_RCC_env_creation_in_progress = $RMKTmpDir + "\rcc_env_creation_in_progress.lock"
	# how many minutes to wait for a/any single RCC env creation to be finished (maxage of $Flagfile_RCC_env_creation_in_progress)
	$Global:RCC_env_max_creation_minutes = 1

	# RCC namespaces
	# - controller
	$Global:rcc_ctrl_rmk = "robotmk"
	# - space for agent and output
	$Global:rcc_space_rmk_agent = "agent"
	$Global:rcc_space_rmk_output = "output"


}




#   _      ____   _____ 
#  | |    / __ \ / ____|
#  | |   | |  | | |  __ 
#  | |   | |  | | | |_ |
#  | |___| |__| | |__| |
#  |______\____/ \_____|
                      
                      


function Log {
	#[CmdletBinding()]
	param(
		[Parameter()]		
		[ValidateNotNullOrEmpty()]
		[string]$Level,				
		[Parameter()]
		[ValidateNotNullOrEmpty()]
		[string]$Message,
		[Parameter()]
		[ValidateNotNullOrEmpty()]
		[string]$file = "$RMKLogfile"		
	)
	$LogTime = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffK")
	$PaddedLevel = $Level.PadRight(6)
	$mypid = $PID.ToString()
	$MsgArr = $Message.Split([System.Environment]::NewLine, [System.StringSplitOptions]::RemoveEmptyEntries)
	if (($MODE -eq "") -or ($MODE -eq $nul)) {
		$EXEC_PHASE = "P1"
		$pidstring = "[${mypid}]".PadRight(8)
	}
	elseif ($MODE -eq "start") {
		$EXEC_PHASE = "P2"
		$myppid = $PPID.ToString()
		$pidstring = "[${myppid}> ${mypid}]".PadRight(16)
	}
	else {
		$EXEC_PHASE = "P-"
	}
	# if length of $MsgArr is more than 1, then we have a multiline message
	if ($MsgArr.Length -gt 1) {
		$prefix = "  |   "
	}
	else {
		$prefix = ""
	}
	$MsgArr | ForEach-Object { "$LogTime ${pidstring} ${EXEC_PHASE} ${PaddedLevel}  ${prefix}$_" >> "$file" } 
	#"$logTime - $PadLevel ${PaddedPID} $Message" >> "$file"
}

function LogInfo {
	param(
		[Parameter()]
		[ValidateNotNullOrEmpty()]
		[string]$Message,
		[Parameter()]
		[ValidateNotNullOrEmpty()]
		[string]$file = "$RMKLogfile"		
	)
	Log "INFO" $Message $file
}

function LogDebug {
	param(
		[Parameter()]
		[ValidateNotNullOrEmpty()]
		[string]$Message,
		[Parameter()]
		[ValidateNotNullOrEmpty()]
		[string]$file = "$RMKLogfile"		
	)
	if ($DEBUG) {
		Log "DEBUG" $Message $file
	}
	
}

function LogError {
	param(
		[Parameter()]
		[ValidateNotNullOrEmpty()]
		[string]$Message,
		[Parameter()]
		[ValidateNotNullOrEmpty()]
		[string]$file = "$RMKLogfile"		
	)
	Log "ERROR" $Message $file
}

function LogWarn {
	param(
		[Parameter()]
		[ValidateNotNullOrEmpty()]
		[string]$Message,
		[Parameter()]
		[ValidateNotNullOrEmpty()]
		[string]$file = "$RMKLogfile"		
	)
	Log "WARN" $Message $file
}

function LogConfiguration {
	param(
		[Parameter()]
		[ValidateNotNullOrEmpty()]
		[string]$Message,
		[Parameter()]
		[ValidateNotNullOrEmpty()]
		[string]$file = "$RMKLogfile"		
	)
	LogDebug "--- 8< --------------------"
	LogDebug "CONFIGURATION:"
	LogDebug "- this script: $scriptFullName"
	LogDebug "- Agent Service Scriptname: $RMK_Agent"
	LogDebug "- PID: $PID"
	LogDebug "- RMKLogDir: $RMKLogDir"
	LogDebug "- RMKTmpDir: $RMKTmpDir"
	LogDebug "- Use RCC: $UseRCC"
	if ($UseRCC) {
		LogRCCConfig
	}
	LogDebug "-------------------- >8 ---"
}

function LogRCCConfig {
	LogDebug "RCC CONFIGURATION:"
	LogDebug "- ROBOCORP_HOME: $ROBOCORP_HOME"	
	LogDebug "- RCCEXE: $RCCEXE"	
	LogDebug "- RMKCfgDir: $RMKCfgDir"
	LogDebug "- Robotmk RCC holotree spaces:"
	LogDebug "  - Robotmk agent: rcc.$rcc_ctrl_rmk/$rcc_space_rmk_agent"
	LogDebug "  - Robotmk output: rcc.$rcc_ctrl_rmk/$rcc_space_rmk_output"
}

function Write-ServiceStatus {
	$status = RMKAgentStatus		
	Write-Host "$RMK_AgentServiceName is $status"	
}

#   _____   _____ _____ ______ _______      _______ _____ ______ 
#  |  __ \ / ____/ ____|  ____|  __ \ \    / /_   _/ ____|  ____|
#  | |__) | (___| (___ | |__  | |__) \ \  / /  | || |    | |__   
#  |  ___/ \___ \\___ \|  __| |  _  / \ \/ /   | || |    |  __|  
#  | |     ____) |___) | |____| | \ \  \  /   _| || |____| |____ 
#  |_|    |_____/_____/|______|_|  \_\  \/   |_____\_____|______|
                                                               
                                                               

#-----------------------------------------------------------------------------#
#                                                                             #
#   Function        Start-PSThread                                            #
#                                                                             #
#   Description     Start a new PowerShell thread                             #
#                                                                             #
#   Arguments       See the Param() block                                     #
#                                                                             #
#   Notes           Returns a thread description object.                      #
#                   The completion can be tested in $_.Handle.IsCompleted     #
#                   Alternative: Use a thread completion event.               #
#                                                                             #
#   References                                                                #
#    https://learn-powershell.net/tag/runspace/                               #
#    https://learn-powershell.net/2013/04/19/sharing-variables-and-live-objects-between-powershell-runspaces/
#    http://www.codeproject.com/Tips/895840/Multi-Threaded-PowerShell-Cookbook
#                                                                             #
#-----------------------------------------------------------------------------#

$PSThreadCount = 0              # Counter of PSThread IDs generated so far
$PSThreadList = @{}             # Existing PSThreads indexed by Id

Function Get-PSThread () {
	Param(
		[Parameter(Mandatory = $false, ValueFromPipeline = $true, Position = 0)]
		[int[]]$Id = $PSThreadList.Keys     # List of thread IDs
	)
	$Id | % { $PSThreadList.$_ }
}

Function Start-PSThread () {
	Param(
		[Parameter(Mandatory = $true, Position = 0)]
		[ScriptBlock]$ScriptBlock, # The script block to run in a new thread
		[Parameter(Mandatory = $false)]
		[String]$Name = "", # Optional thread name. Default: "PSThread$Id"
		[Parameter(Mandatory = $false)]
		[String]$Event = "", # Optional thread completion event name. Default: None
		[Parameter(Mandatory = $false)]
		[Hashtable]$Variables = @{}, # Optional variables to copy into the script context.
		[Parameter(Mandatory = $false)]
		[String[]]$Functions = @(), # Optional functions to copy into the script context.
		[Parameter(Mandatory = $false)]
		[Object[]]$Arguments = @()          # Optional arguments to pass to the script.
	)

	$Id = $script:PSThreadCount
	$script:PSThreadCount += 1
	if (!$Name.Length) {
		$Name = "PSThread$Id"
	}
	$InitialSessionState = [System.Management.Automation.Runspaces.InitialSessionState]::CreateDefault()
	foreach ($VarName in $Variables.Keys) {
		# Copy the specified variables into the script initial context
		$value = $Variables.$VarName
		LogDebug "Adding variable $VarName=[$($Value.GetType())]$Value"
		$var = New-Object System.Management.Automation.Runspaces.SessionStateVariableEntry($VarName, $value, "")
		$InitialSessionState.Variables.Add($var)
	}
	foreach ($FuncName in $Functions) {
		# Copy the specified functions into the script initial context
		$Body = Get-Content function:$FuncName
		#LogDebug "Adding function $FuncName () {$Body}"
		LogDebug "Adding function $FuncName()"
		$func = New-Object System.Management.Automation.Runspaces.SessionStateFunctionEntry($FuncName, $Body)
		$InitialSessionState.Commands.Add($func)
	}
	$RunSpace = [RunspaceFactory]::CreateRunspace($InitialSessionState)
	$RunSpace.Open()
	$PSPipeline = [powershell]::Create()
	$PSPipeline.Runspace = $RunSpace
	$PSPipeline.AddScript($ScriptBlock) | Out-Null
	$Arguments | % {
		LogDebug "Adding argument [$($_.GetType())]'$_'"
		$PSPipeline.AddArgument($_) | Out-Null
	}
	$Handle = $PSPipeline.BeginInvoke() # Start executing the script
	if ($Event.Length) {
		# Do this after BeginInvoke(), to avoid getting the start event.
		Register-ObjectEvent $PSPipeline -EventName InvocationStateChanged -SourceIdentifier $Name -MessageData $Event
	}
	$PSThread = New-Object PSObject -Property @{
		Id         = $Id
		Name       = $Name
		Event      = $Event
		RunSpace   = $RunSpace
		PSPipeline = $PSPipeline
		Handle     = $Handle
	}     # Return the thread description variables
	$script:PSThreadList[$Id] = $PSThread
	$PSThread
}

#-----------------------------------------------------------------------------#
#                                                                             #
#   Function        Receive-PSThread                                          #
#                                                                             #
#   Description     Get the result of a thread, and optionally clean it up    #
#                                                                             #
#   Arguments       See the Param() block                                     #
#                                                                             #
#-----------------------------------------------------------------------------#

Function Receive-PSThread () {
	[CmdletBinding()]
	Param(
		[Parameter(Mandatory = $false, ValueFromPipeline = $true, Position = 0)]
		[PSObject]$PSThread, # Thread descriptor object
		[Parameter(Mandatory = $false)]
		[Switch]$AutoRemove                 # If $True, remove the PSThread object
	)
	Process {
		if ($PSThread.Event -and $AutoRemove) {
			Unregister-Event -SourceIdentifier $PSThread.Name
			Get-Event -SourceIdentifier $PSThread.Name | Remove-Event # Flush remaining events
		}
		try {
			$PSThread.PSPipeline.EndInvoke($PSThread.Handle) # Output the thread pipeline output
		}
		catch {
			$_ # Output the thread pipeline error
		}
		if ($AutoRemove) {
			$PSThread.RunSpace.Close()
			$PSThread.PSPipeline.Dispose()
			$PSThreadList.Remove($PSThread.Id)
		}
	}
}

Function Remove-PSThread () {
	[CmdletBinding()]
	Param(
		[Parameter(Mandatory = $false, ValueFromPipeline = $true, Position = 0)]
		[PSObject]$PSThread                 # Thread descriptor object
	)
	Process {
		$_ | Receive-PSThread -AutoRemove | Out-Null
	}
}

#-----------------------------------------------------------------------------#
#                                                                             #
#   Function        Send-PipeMessage                                          #
#                                                                             #
#   Description     Send a message to a named pipe                            #
#                                                                             #
#   Arguments       See the Param() block                                     #
#                                                                             #
#-----------------------------------------------------------------------------#

Function Send-PipeMessage () {
	Param(
		[Parameter(Mandatory = $true)]
		[String]$RMK_AgentPipeName, # Named pipe name
		[Parameter(Mandatory = $true)]
		[String]$Message            # Message string
	)
	$PipeDir = [System.IO.Pipes.PipeDirection]::Out
	$PipeOpt = [System.IO.Pipes.PipeOptions]::Asynchronous

	$pipe = $null # Named pipe stream
	$sw = $null   # Stream Writer
	try {
		$pipe = new-object System.IO.Pipes.NamedPipeClientStream(".", $RMK_AgentPipeName, $PipeDir, $PipeOpt)
		$sw = new-object System.IO.StreamWriter($pipe)
		$pipe.Connect(1000)
		if (!$pipe.IsConnected) {
			throw "Failed to connect client to pipe $RMK_AgentPipeName"
		}
		$sw.AutoFlush = $true
		$sw.WriteLine($Message)
	}
	catch {
		LogError "Error sending pipe $RMK_AgentPipeName message: $_"
	}
	finally {
		if ($sw) {
			$sw.Dispose() # Release resources
			$sw = $null   # Force the PowerShell garbage collector to delete the .net object
		}
		if ($pipe) {
			$pipe.Dispose() # Release resources
			$pipe = $null   # Force the PowerShell garbage collector to delete the .net object
		}
	}
}

#-----------------------------------------------------------------------------#
#                                                                             #
#   Function        Receive-PipeMessage                                       #
#                                                                             #
#   Description     Wait for a message from a named pipe                      #
#                                                                             #
#   Arguments       See the Param() block                                     #
#                                                                             #
#   Notes           I tried keeping the pipe open between client connections, #
#                   but for some reason everytime the client closes his end   #
#                   of the pipe, this closes the server end as well.          #
#                   Any solution on how to fix this would make the code       #
#                   more efficient.                                           #
#-----------------------------------------------------------------------------#

Function Receive-PipeMessage () {
	Param(
		[Parameter(Mandatory = $true)]
		[String]$RMK_AgentPipeName           # Named pipe name
	)
	$PipeDir = [System.IO.Pipes.PipeDirection]::In
	$PipeOpt = [System.IO.Pipes.PipeOptions]::Asynchronous
	$PipeMode = [System.IO.Pipes.PipeTransmissionMode]::Message

	try {
		$pipe = $null       # Named pipe stream
		$pipe = New-Object system.IO.Pipes.NamedPipeServerStream($RMK_AgentPipeName, $PipeDir, 1, $PipeMode, $PipeOpt)
		$sr = $null         # Stream Reader
		$sr = new-object System.IO.StreamReader($pipe)
		$pipe.WaitForConnection()
		$Message = $sr.Readline()
		$Message
	}
	catch {
		LogError "Error receiving pipe message: $_"
	}
	finally {
		if ($sr) {
			$sr.Dispose() # Release resources
			$sr = $null   # Force the PowerShell garbage collector to delete the .net object
		}
		if ($pipe) {
			$pipe.Dispose() # Release resources
			$pipe = $null   # Force the PowerShell garbage collector to delete the .net object
		}
	}
}

#-----------------------------------------------------------------------------#
#                                                                             #
#   Function        Start-PipeHandlerThread                                   #
#                                                                             #
#   Description     Start a new thread waiting for control messages on a pipe #
#                                                                             #
#   Arguments       See the Param() block                                     #
#                                                                             #
#   Notes           The pipe handler script uses function Receive-PipeMessage.#
#                   This function must be copied into the thread context.     #
#                                                                             #
#                   The other functions and variables copied into that thread #
#                   context are not strictly necessary, but are useful for    #
#                   debugging possible issues.                                #
#-----------------------------------------------------------------------------#

$pipeThreadName = "Control Pipe Handler"

Function Start-PipeHandlerThread () {
	Param(
		[Parameter(Mandatory = $true)]
		[String]$RMK_AgentPipeName, # Named pipe name
		[Parameter(Mandatory = $false)]
		[String]$Event = "ControlMessage"   # Event message
	)
	$currentUserName = Get-CurrentUserName

	Start-PSThread -Variables @{  # Copy variables required by function Log() into the thread context
		logDir          = $RMKLogDir
		logFile         = $RMKLogfile
		currentUserName = $currentUserName
	} -Functions Now, Log, Receive-PipeMessage -ScriptBlock {
		Param($RMK_AgentPipeName, $pipeThreadName)
		try {
			Receive-PipeMessage "$RMK_AgentPipeName" # Blocks the thread until the next message is received from the pipe
		}
		catch {
			LogInfo "$pipeThreadName # Error: $_"
			throw $_ # Push the error back to the main thread
		}
	} -Name $pipeThreadName -Event $Event -Arguments $RMK_AgentPipeName, $pipeThreadName
}

#-----------------------------------------------------------------------------#
#                                                                             #
#   Function        Receive-PipeHandlerThread                                 #
#                                                                             #
#   Description     Get what the pipe handler thread received                 #
#                                                                             #
#   Arguments       See the Param() block                                     #
#                                                                             #
#   Notes                                                                     #
#-----------------------------------------------------------------------------#

Function Receive-PipeHandlerThread () {
	Param(
		[Parameter(Mandatory = $true)]
		[PSObject]$pipeThread               # Thread descriptor
	)
	Receive-PSThread -PSThread $pipeThread -AutoRemove
}

#-----------------------------------------------------------------------------#
#                                                                             #
#   Function        $source                                                   #
#                                                                             #
#   Description     C# source of the PSService.exe stub                       #
#                                                                             #
#   Arguments                                                                 #
#                                                                             #
#   Notes           The lines commented with "SET STATUS" and "EVENT LOG" are #
#                   optional. (Or blocks between "// SET STATUS [" and        #
#                   "// SET STATUS ]" comments.)                              #
#                   SET STATUS lines are useful only for services with a long #
#                   startup time.                                             #
#                   EVENT LOG lines are useful for debugging the service.     #
#                                                                             #
#-----------------------------------------------------------------------------#


$source = @"
  using System;
  using System.ServiceProcess;
  using System.Diagnostics;
  using System.Runtime.InteropServices;                                 // SET STATUS
  using System.ComponentModel;                                          // SET STATUS

  public enum ServiceType : int {                                       // SET STATUS [
    SERVICE_WIN32_OWN_PROCESS = 0x00000010,
    SERVICE_WIN32_SHARE_PROCESS = 0x00000020,
  };                                                                    // SET STATUS ]

  public enum ServiceState : int {                                      // SET STATUS [
    SERVICE_STOPPED = 0x00000001,
    SERVICE_START_PENDING = 0x00000002,
    SERVICE_STOP_PENDING = 0x00000003,
    SERVICE_RUNNING = 0x00000004,
    SERVICE_CONTINUE_PENDING = 0x00000005,
    SERVICE_PAUSE_PENDING = 0x00000006,
    SERVICE_PAUSED = 0x00000007,
  };                                                                    // SET STATUS ]

  [StructLayout(LayoutKind.Sequential)]                                 // SET STATUS [
  public struct ServiceStatus {
    public ServiceType dwServiceType;
    public ServiceState dwCurrentState;
    public int dwControlsAccepted;
    public int dwWin32ExitCode;
    public int dwServiceSpecificExitCode;
    public int dwCheckPoint;
    public int dwWaitHint;
  };                                                                    // SET STATUS ]

  public enum Win32Error : int { // WIN32 errors that we may need to use
    NO_ERROR = 0,
    ERROR_APP_INIT_FAILURE = 575,
    ERROR_FATAL_APP_EXIT = 713,
    ERROR_SERVICE_NOT_ACTIVE = 1062,
    ERROR_EXCEPTION_IN_SERVICE = 1064,
    ERROR_SERVICE_SPECIFIC_ERROR = 1066,
    ERROR_PROCESS_ABORTED = 1067,
  };

  public class Service_$RMK_AgentServiceName : ServiceBase { // $RMK_AgentServiceName may begin with a digit; The class name must begin with a letter
    private System.Diagnostics.EventLog eventLog;                       // EVENT LOG
    private ServiceStatus serviceStatus;                                // SET STATUS

    public Service_$RMK_AgentServiceName() {
      ServiceName = "$RMK_AgentServiceName";
      CanStop = true;
      CanPauseAndContinue = false;
      AutoLog = true;

      eventLog = new System.Diagnostics.EventLog();                     // EVENT LOG [
      if (!System.Diagnostics.EventLog.SourceExists(ServiceName)) {         
        System.Diagnostics.EventLog.CreateEventSource(ServiceName, "$EventLog");
      }
      eventLog.Source = ServiceName;
      eventLog.Log = "$EventLog";                                        // EVENT LOG ]
      EventLog.WriteEntry(ServiceName, "$RMK_AgentServiceName() for $RMK_AgentExeName initialized.");      // EVENT LOG
    }

    [DllImport("advapi32.dll", SetLastError=true)]                      // SET STATUS
    private static extern bool SetServiceStatus(IntPtr handle, ref ServiceStatus serviceStatus);

    protected override void OnStart(string [] args) {
      EventLog.WriteEntry(ServiceName, "$RMK_AgentServiceName.OnStart()"); // EVENT LOG
      // Set the service state to Start Pending.                        // SET STATUS [
      // Only useful if the startup time is long. Not really necessary here for a 2s startup time.
      serviceStatus.dwServiceType = ServiceType.SERVICE_WIN32_OWN_PROCESS;
      serviceStatus.dwCurrentState = ServiceState.SERVICE_START_PENDING;
      serviceStatus.dwWin32ExitCode = 0;
      serviceStatus.dwWaitHint = 2000; // It takes about 2 seconds to start PowerShell
      SetServiceStatus(ServiceHandle, ref serviceStatus);               // SET STATUS ]
      // Start a child process with another copy of this script
      try {
        Process p = new Process();
        // Redirect the output stream of the child process.
        p.StartInfo.UseShellExecute = false;
        p.StartInfo.RedirectStandardOutput = true;
        p.StartInfo.FileName = "PowerShell.exe";
		// Ref 22db44
        p.StartInfo.Arguments = "-ExecutionPolicy Bypass -c & '$RMK_AgentFullNameEscaped' -SCMStart"; // Works if path has spaces, but not if it contains ' quotes.
		EventLog.WriteEntry(ServiceName, "$RMK_AgentServiceName.OnStart(): Executing: '$RMK_AgentFullNameEscaped' -SCMStart"); // EVENT LOG
        p.Start();
        // Read the output stream first and then wait. (To avoid deadlocks says Microsoft!)
        string output = p.StandardOutput.ReadToEnd();
        // Wait for the completion of the script startup code, that launches the -Service instance
        p.WaitForExit();
		EventLog.WriteEntry(ServiceName, "$RMK_AgentServiceName.OnStart(): SCMStart came back with exit code " + p.ExitCode); // EVENT LOG
        if (p.ExitCode != 0) throw new Win32Exception((int)(Win32Error.ERROR_APP_INIT_FAILURE));
        // Success. Set the service state to Running.                   // SET STATUS
        serviceStatus.dwCurrentState = ServiceState.SERVICE_RUNNING;    // SET STATUS
      } catch (Exception e) {
        EventLog.WriteEntry(ServiceName, "$RMK_AgentServiceName.OnStart(): // Failed to start $RMK_AgentFullNameEscaped. " + e.Message, EventLogEntryType.Error); // EVENT LOG
        // Change the service state back to Stopped.                    // SET STATUS [
        serviceStatus.dwCurrentState = ServiceState.SERVICE_STOPPED;
        Win32Exception w32ex = e as Win32Exception; // Try getting the WIN32 error code
        if (w32ex == null) { // Not a Win32 exception, but maybe the inner one is...
          w32ex = e.InnerException as Win32Exception;
        }    
        if (w32ex != null) {    // Report the actual WIN32 error
          serviceStatus.dwWin32ExitCode = w32ex.NativeErrorCode;
        } else {                // Make up a reasonable reason
          serviceStatus.dwWin32ExitCode = (int)(Win32Error.ERROR_APP_INIT_FAILURE);
        }                                                               // SET STATUS ]
      } finally {
        serviceStatus.dwWaitHint = 0;                                   // SET STATUS
        SetServiceStatus(ServiceHandle, ref serviceStatus);             // SET STATUS
        EventLog.WriteEntry(ServiceName, "$RMK_AgentExeName OnStart() // Exit"); // EVENT LOG
      }
    }

    protected override void OnStop() {
      EventLog.WriteEntry(ServiceName, "$RMK_AgentExeName OnStop() // Entry");   // EVENT LOG
      // Start a child process with another copy of ourselves
      try {
        Process p = new Process();
        // Redirect the output stream of the child process.
        p.StartInfo.UseShellExecute = false;
        p.StartInfo.RedirectStandardOutput = true;
        p.StartInfo.FileName = "PowerShell.exe";
		// Ref 6e3aaf
        p.StartInfo.Arguments = "-ExecutionPolicy Bypass -c & '$RMK_AgentFullNameEscaped' -SCMStop"; // Works if path has spaces, but not if it contains ' quotes.
        p.Start();
        // Read the output stream first and then wait. (To avoid deadlocks says Microsoft!)
        string output = p.StandardOutput.ReadToEnd();
        // Wait for the PowerShell script to be fully stopped.
        p.WaitForExit();
        if (p.ExitCode != 0) throw new Win32Exception((int)(Win32Error.ERROR_APP_INIT_FAILURE));
        // Success. Set the service state to Stopped.                   // SET STATUS
        serviceStatus.dwCurrentState = ServiceState.SERVICE_STOPPED;      // SET STATUS
      } catch (Exception e) {
        EventLog.WriteEntry(ServiceName, "$RMK_AgentExeName OnStop() // Failed to stop $RMK_AgentFullNameEscaped. " + e.Message, EventLogEntryType.Error); // EVENT LOG
        // Change the service state back to Started.                    // SET STATUS [
        serviceStatus.dwCurrentState = ServiceState.SERVICE_RUNNING;
        Win32Exception w32ex = e as Win32Exception; // Try getting the WIN32 error code
        if (w32ex == null) { // Not a Win32 exception, but maybe the inner one is...
          w32ex = e.InnerException as Win32Exception;
        }    
        if (w32ex != null) {    // Report the actual WIN32 error
          serviceStatus.dwWin32ExitCode = w32ex.NativeErrorCode;
        } else {                // Make up a reasonable reason
          serviceStatus.dwWin32ExitCode = (int)(Win32Error.ERROR_APP_INIT_FAILURE);
        }                                                               // SET STATUS ]
      } finally {
        serviceStatus.dwWaitHint = 0;                                   // SET STATUS
        SetServiceStatus(ServiceHandle, ref serviceStatus);             // SET STATUS
        EventLog.WriteEntry(ServiceName, "$RMK_AgentExeName OnStop() // Exit"); // EVENT LOG
      }
    }

    public static void Main() {
      System.ServiceProcess.ServiceBase.Run(new Service_$RMK_AgentServiceName());
    }
  }
"@

main