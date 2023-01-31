
# Credits to https://github.com/FuzzySecurity/PowerShell-Suite/blob/master/Invoke-CreateProcess.ps1

$scriptname = (Get-Item -Path $MyInvocation.MyCommand.Path).BaseName
# read mode from args or set to 0
$MODE = if ($args[0]) { $args[0] } else { $nul };
$PPID = if ($args[1]) { $args[1] } else { $nul };

$DEBUG = $true
#$DEBUG = $false


$UseRCC = $true



# Execution phase: 
# 1 = started by Agent, with parent process
# 2 = started by itself detached, without parent process
$EXEC_PHASE = "-"


function main() {
	# robotmk.ps1 : start Robotmk to produce output
	# robotmk-ctrl.ps1 : start Robotmk to control the daemon
	SetScriptVars
	
	Ensure-Directory $RMKlogdir
	Ensure-Directory $RMKTmpDir
	Ensure-Directory $ROBOCORP_HOME
	LogConfig
	
	if ($scriptname -match ".*robotmk$") {
		StartAgentOutput
	}
	elseif ($scriptname -match ".*robotmk-ctrl") {
		TouchFile $controller_deadman_file	"Controller deadman file"
		# FIXME: start Daemoncontroller in any case. It must also check if the conda blueprint 
		# changed meanwhile. If so, it must restart the daemon.
		DaemonController($MODE)
		
	}
 else {
		Write-Host "ERROR: Unknown script name: $scriptname"
	}
}

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

function StartAgentOutput {
	LogInfo "--- Starting Robotmk Agent Output mode"
	if ($UseRCC) {
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

function DaemonController {
	# mode=start/stop/restart
	# CAVEAT: using the Daemon control words (start/stop etc) will start the Daemon in the 
	# user context. This is not what we probably want. The Daemon should better in the system context.
	param (
		[Parameter(Mandatory = $False)]
		[string]$mode = $null
	)  
	if ($mode -eq "") {
		LogInfo "---- Script was started without mode (by Agent?); have to start myself again to damonize."
		StartControllerDecoupled

	}
 elseif ($mode -eq "start") {
		LogInfo "---- Script was started with mode 'start'; unless started by hand (?), it is now an independent process and can control the Robotmk Agent Daemon... "
		RobotmkController
	}
 elseif ($mode -eq "stop") {
		LogInfo "---- Script was started with mode 'stop': Trying to kill Robotmk daemon..."
		LogError "TODO: kill daemon not implemented yet"
		
	}
 elseif ($mode -eq "restart") {
		# kill daemon
		LogInfo "---- Script was started with mode 'restart': Trying to kill & start Robotmk daemon..."
		LogError "TODO: kill daemon not implemented yet"
		# start daemon
		Write-Host "TODO: start daemon"
		DaemonController
	}
} 

function RobotmkController {
	# Tasks of the controller: 
	# use RCC? 
	# yes:
	# - check if RCC env is ready 
	# - check if Agent runs 
	# no: 
	# - check if native python env is ready
	# Starts the Robotmk process with RCC or native Python
	# TODO: How to make RCC execution an optional feature?
	if ($UseRCC) {
		$blueprint = GetCondaBlueprint $RMKCfgDir\conda.yaml			
		
		if ( IsRCCEnvReady $blueprint) {
			# if the RCC environment is ready, start the Agent if not yet running
			LogInfo "Robotmk RCC environment is ready to use."
			if (IsRobotmkAgentRunning) {
				LogInfo "Nothing to do, Robotmk Agent is already running."
			}
			else {
				RunRobotmkTask "agent"
			}			
		}		
		else {	
			# otherwise, try to create the environment	
			if (IsFlagfileYoungerThanMinutes $Flagfile_RCC_env_creation_in_progress $RCC_env_max_creation_minutes) {
				LogWarn "Robotmk RCC environment is NOT ready to use."
				LogWarn "Another Robotmk RCC environment creation is in progress (flagfile $Flagfile_RCC_env_creation_in_progress present and younger than $RCC_env_max_creation_minutes min). Exiting."
				return
			}
			else {
				LogWarn "RCC environment is NOT ready to use."
				LogWarn "Will now try to create a new RCC environment."
				RemoveFlagfile $Flagfile_RCC_env_robotmk_ready
				TouchFile $Flagfile_RCC_env_creation_in_progress "RCC creation state file"
				if (Test-Path ($RMKCfgDir + "\hololib.zip")) {
					LogInfo "hololib.zip found in $RMKCfgDir, importing it"
					RCCImportHololib "$RMKCfgDir\hololib.zip"
					# TODO: create spaces for agent /output?
				}
				else {
					LogInfo "Catalog must be created from network (hololib.zip not found in $RMKCfgDir)"		
					# Create a separate Holotree Space for agent and output	
					RCCEnvironmentCreate "$RMKCfgDir\robot.yaml" $rcc_ctrl_rmk $rcc_space_rmk_agent
					RCCEnvironmentCreate "$RMKCfgDir\robot.yaml" $rcc_ctrl_rmk $rcc_space_rmk_output
				}
				# This takes some minutes... 
				# Watch the progress with `rcc ht list` and `rcc ht catalogs`. First the catalog is created, then
				# both spaces.
				if (CatalogContainsAgentBlueprint $blueprint) {
					TouchFile $Flagfile_RCC_env_robotmk_ready "RCC env ready flagfile"
					RemoveFlagfile $Flagfile_RCC_env_creation_in_progress	
					LogInfo "OK: Environments for Robotmk created and ready to use on next run. Exiting now."		
				}
				else {
					LogInfo "RCC environment creation for Robotmk agent failed for some reason. Exiting."
					RemoveFlagfile $Flagfile_RCC_env_creation_in_progress
				}
			}

		}		
		
	}
	else {
		# TODO: finalize native python execution
		$Binary = $PythonExe
		$Arguments = "$PythonExe $RobotmkAgent"
	}
	

}

function StartControllerDecoupled {
	# Starts the Robotmk process decoupled from the current process
	# Hand over the PID of calling process and log it
	$powershell = (Get-Command powershell.exe).Path
	DetachProcess $powershell "-File $PSCommandPath start ${PID}"
	LogInfo "Exiting... (Daemon will run in background now)"
	# sleep  100 seconds to give the daemon some time to start
	# Start-Sleep -s 100

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



function DetachProcess {
	param (
		[Parameter(Mandatory = $True)]
		[string]$Binary,
		[Parameter(Mandatory = $False)]
		[string]$Arguments = $null
	)  
	# Define all the structures for CreateProcess
	Add-Type -TypeDefinition @"
	using System;
	using System.Diagnostics;
	using System.Runtime.InteropServices;

	[Flags]
	public enum CreationFlags : int
	{
		NONE = 0,
		DEBUG_PROCESS = 0x00000001,
		DEBUG_ONLY_THIS_PROCESS = 0x00000002,
		CREATE_SUSPENDED = 0x00000004,
		DETACHED_PROCESS = 0x00000008,
		CREATE_NEW_CONSOLE = 0x00000010,
		CREATE_NEW_PROCESS_GROUP = 0x00000200,
		CREATE_UNICODE_ENVIRONMENT = 0x00000400,
		CREATE_SEPARATE_WOW_VDM = 0x00000800,
		CREATE_SHARED_WOW_VDM = 0x00001000,
		CREATE_PROTECTED_PROCESS = 0x00040000,
		EXTENDED_STARTUPINFO_PRESENT = 0x00080000,
		CREATE_BREAKAWAY_FROM_JOB = 0x01000000,
		CREATE_PRESERVE_CODE_AUTHZ_LEVEL = 0x02000000,
		CREATE_DEFAULT_ERROR_MODE = 0x04000000,
		CREATE_NO_WINDOW = 0x08000000,
	}	

	[StructLayout(LayoutKind.Sequential)]
	public struct PROCESS_INFORMATION
	{
		public IntPtr hProcess; public IntPtr hThread; public uint dwProcessId; public uint dwThreadId;
	}
	
	[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
	public struct STARTUPINFO
	{
		public uint cb; public string lpReserved; public string lpDesktop; public string lpTitle;
		public uint dwX; public uint dwY; public uint dwXSize; public uint dwYSize; public uint dwXCountChars;
		public uint dwYCountChars; public uint dwFillAttribute; public uint dwFlags; public short wShowWindow;
		public short cbReserved2; public IntPtr lpReserved2; public IntPtr hStdInput; public IntPtr hStdOutput;
		public IntPtr hStdError;
	}
	
	[StructLayout(LayoutKind.Sequential)]
	public struct SECURITY_ATTRIBUTES
	{
		public int length; public IntPtr lpSecurityDescriptor; public bool bInheritHandle;
	}
	
	public static class Kernel32
	{
		[DllImport("kernel32.dll", SetLastError=true)]
		public static extern bool CreateProcess(
			string lpApplicationName, string lpCommandLine, ref SECURITY_ATTRIBUTES lpProcessAttributes, 
			ref SECURITY_ATTRIBUTES lpThreadAttributes, bool bInheritHandles, uint dwCreationFlags, 
			IntPtr lpEnvironment, string lpCurrentDirectory, ref STARTUPINFO lpStartupInfo, 
			out PROCESS_INFORMATION lpProcessInformation);
	}
"@
	# StartupInfo Struct
	$StartupInfo = New-Object STARTUPINFO
	$StartupInfo.dwFlags = 0x1
	$StartupInfo.wShowWindow = 0x0001 
	$StartupInfo.cb = [System.Runtime.InteropServices.Marshal]::SizeOf($StartupInfo) # Struct Size
	
	# ProcessInfo Struct
	$ProcessInfo = New-Object PROCESS_INFORMATION
	
	# SECURITY_ATTRIBUTES Struct (Process & Thread)
	$SecAttr = New-Object SECURITY_ATTRIBUTES
	$SecAttr.Length = [System.Runtime.InteropServices.Marshal]::SizeOf($SecAttr)
	
	# CreateProcess --> lpCurrentDirectory
	$cwd = (Get-Item -Path ".\" -Verbose).FullName
	
	# https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags
	# - For console processes, the new process does not inherit its parent's console (the default). T
	$DETACHED_PROCESS = 0x00000008 
	# - The new process is the root process of a new process group. The process group includes all processes that are descendants of this root process. 
	$CREATE_NEW_PROCESS_GROUP = 0x00000200 
	# - The process is a console application that is being run without a console window.
	# TODO: Check if this is needed  
	$CREATE_NO_WINDOW = 0x08000000 

	# merge creation flags:
	# 1) All three flags work together when executing e.g. RCC.exe 
	#$CreationFlags = $CreationFlags -bor $DETACHED_PROCESS -bor $CREATE_NEW_PROCESS_GROUP -bor $CREATE_NO_WINDOW
	# 2) But Starting a Powershell only works if $DETACHED_PROCESS is not set. 
	$CreationFlags = $CreationFlags -bor $CREATE_NEW_PROCESS_GROUP -bor $CREATE_NO_WINDOW
	# convert to int 
	$CreationFlagsInt = [int]$CreationFlags
	


	# $binary must be an absolute path!!
	LogInfo "!! $Binary $Arguments"
	
	# TODO: How to disable black command windows?
	#[Kernel32]::CreateProcess($Binary, $Arguments, [ref] $SecAttr, [ref] $SecAttr, $false, $CreationFlagsInt, [IntPtr]::Zero, $cwd, [ref] $StartupInfo, [ref] $ProcessInfo) | out-null

	$Arguments = "$Binary $Arguments"
	[Kernel32]::CreateProcess(
		$Binary, 
		$Arguments, 
		[ref] $SecAttr, 
		[ref] $SecAttr,
		$false, 
		$CreationFlagsInt,
		[IntPtr]::Zero, 
		$cwd, 
		[ref] $StartupInfo, 
		[ref] $ProcessInfo
	) 
	#Write-Host $ProcessInfo.dwProcessId
}

function IsRobotmkAgentRunning {
	# TODO: can only see own processes! 
	$processes = GetProcesses -Cmdline "%robotmk.exe agent bg"
	# if length of array is 0, no process is running
	if ($processes.Length -eq 0) {
		if (Test-Path $pidfile) {
			LogInfo "No process 'robotmk.exe agent bg' is running, removing stale PID file $pidfile."
			Remove-Item $pidfile -Force -ErrorAction SilentlyContinue
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
		if (Test-path $pidfile) {
			$pidfromfile = Get-Content $pidfile
			# if pidfromfile is in the list of running processes, we are good
			if ($processes -contains $pidfromfile) {
				LogDebug "The PID $pidfromfile is already running and in pidfile $pidfile."
				return $true
			}
			else {
				LogError "The PID read from $pidfile ($pidfromfile) des NOT seem to run."
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


function GetProcesses {
	param (
		[Parameter(Mandatory = $True)]
		[string]$Cmdline
	)
	#LogInfo '!! Get-WmiObject -Query "SELECT * FROM Win32_Process WHERE CommandLine like "'$Cmdline'" | Select ProcessId'
	#$processId = Get-WmiObject -Query "SELECT * FROM Win32_Process WHERE CommandLine like '$Cmdline'" | Export-Csv -Path c:\robotmk.csv -NoTypeInformation -Encoding ASCII
	# TODO: when run by the agent, no process is found
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
		LogInfo "Directory $directory does not exist, creating it."
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

function SetScriptVars {
	
	$CMKAgentDir = if ($env:CMK_AGENT_DIR) { $env:CMK_AGENT_DIR } else { "x:\ProgramData\checkmk\agent" };
	# Try to read the environment variables from the agent. If not set, use defaults.
	$Global:MK_LOGDIR = Get-EnvVar "MK_LOGDIR" "$CMKAgentDir\log"
	$Global:RMKLogDir = "$MK_LOGDIR\robotmk"
	$Global:MK_TEMPDIR = Get-EnvVar "MK_TEMPDIR" "$CMKAgentDir\tmp"
	$Global:RMKTmpDir = "$MK_TEMPDIR\robotmk"
	$Global:MK_CONFDIR = Get-EnvVar "MK_CONFDIR" "$CMKAgentDir\config"
	$Global:RMKCfgDir = "$MK_CONFDIR\robotmk"
	$Global:RMKLogfile = "$RMKLogDir\${scriptname}-plugin.log"	

	$Global:ROBOCORP_HOME = if ($env:ROBOCORP_HOME) { $env:ROBOCORP_HOME } else { "C:\Users\vagrant\Documents\rc_homes\rcc1" };
	Set-EnvVar "ROBOCORP_HOME" $ROBOCORP_HOME	

	# Expose env vars for CMK agent (they exist if called from agent, but 
	# do NOT if called while developing)
	Set-EnvVar "ROBOTMK_LOGDIR" $RMKLogDir 
	Set-EnvVar "ROBOTMK_TMPDIR" $RMKTmpDir 
	Set-EnvVar "ROBOTMK_CFGDIR" $RMKCfgDir

	# FILES ========================================
	$Global:RCCExe = $CMKAgentDir + "\bin\rcc.exe"
	# Ref 7e8b2c1 (agent.py)
	$Global:pidfile = $RMKTmpDir + "\robotmk_agent.pid"
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

function LogConfig {
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
	LogDebug "- Scriptname: $scriptname"
	LogDebug "- mode: $MODE"
	LogDebug "- PID: $PID"
	LogDebug "- PPID: $PPID"
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

main