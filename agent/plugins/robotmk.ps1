
# Credits to https://github.com/FuzzySecurity/PowerShell-Suite/blob/master/Invoke-CreateProcess.ps1

# read mode from arrgs or set to 0
$mode = if ($args[0]) { $args[0] } else { $nul };

$DEBUG = $true
#$CONTROLLER = if ($env:RMK_CTRL) { $env:RMK_CTRL } else { 1 };
$CONTROLLER = 1

$UseRCC = $true
$PyName = "python"
$PyExe = "C:\Python310\python.exe"
$DaemonName = "daemon.py"


# TODO: Determine Agent dir
#$CMKAgentDir = "C:\ProgramData\check_mk\agent"
$CMKAgentDir = if ($env:CMK_AGENT_DIR) { $env:CMK_AGENT_DIR } else { "C:\Users\vagrant\Documents\01_dev\rmkv2\agent" };
$RCCExe = $CMKAgentDir + "\bin\rcc.exe"
$RobotmkRCCdir = $CMKAgentDir + "\lib\rcc_robotmk"
$CMKtempdir = $CMKAgentDir + "\tmp"

$DaemonPidfile = "robotmk_agent_daemon"
$pidfile = $CMKtempdir + "\" + $DaemonPidfile + ".pid"
$Flagfile_controller_last_execution = $CMKtempdir + "\robotmk_controller_last_execution"
# This flagfile indicates that both there is a usable holotree space for "robotmk agent/output"
$Flagfile_RCC_env_robotmk_ready = $CMKtempdir + "\rcc_env_robotmk_agent_ready"
# IMPORTANT! All other Robot subprocesses must respect this file and not start if it is present!
# (There is only ONE RCC creation allowed at a time.)
$Flagfile_RCC_env_creation_in_progress = $CMKtempdir + "\rcc_env_creation_in_progress.lock"
# how many minutes to wait for a/any single RCC env creation to be finished
$RCC_env_max_creation_minutes = 2

# TODO: How to set system env vars globally? Needed?
#[System.Environment]::SetEnvironmentVariable('ROBOCORP_HOME', 'C:\rcc')
#[System.Environment]::SetEnvironmentVariable('ROBOCORP_HOME', 'C:\Users\vagrant\Documents\rc_homes\rcc1')
$ROBOCORP_HOME = if ($env:ROBOCORP_HOME) { $env:ROBOCORP_HOME } else { "C:\Users\vagrant\Documents\rc_homes\rcc1" };

$rcc_ctrl_rmk = "robotmk"
$rcc_space_rmk_agent = "agent"
$rcc_space_rmk_output = "output"

function main() {
	# robotmk.ps1 : start Robotmk to produce output
	# robotmk-ctrl.ps1 : start Robotmk to control the daemon
	# Both scripts will be mostly identical, but must be separate files in order
	# to be run by the agent. 

	# CONTROLLER is a helper variable for prototyping and switching between
	# the two behaviours
	# if name of this script is robotmk-ctrl.ps1, then CONTROLLER is set to 1
	# if name of this script is robotmk.ps1, then CONTROLLER is set to 0
	# get name of this script
	
	$scriptname = $MyInvocation.ScriptName
	if ($scriptname -match ".*robotmk.ps1") {
		StartAgentOutput
	}
	elseif ($scriptname -match ".*robotmk-ctrl.ps1") {
		$daemon_pid = IsDaemonRunning
		if (-Not ($daemon_pid)) {
			DaemonController($mode)
		}
		else {
			debug "Daemon is already running with PID: $daemon_pid"
		}
		CreateFlagfile $Flagfile_controller_last_execution		
	}
 else {
		Write-Host "ERROR: Unknown script name: $scriptname"
	}
}

function debug() {
	if ($DEBUG) {
		Write-Host "DEBUG: $args"
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
			CreateFlagfile $Flagfile_RCC_env_robotmk_ready			
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
	$condahash = & $RCCExe ht hash $conda_yaml 2>&1
	$m = $condahash -match "Blueprint hash for.*is (?<blueprint>[A-Za-z0-9]*)\."
	$blueprint = $Matches.blueprint
	return $blueprint
}

function CatalogContainsAgentBlueprint {
	param (
		[Parameter(Mandatory = $True)]
		[string]$blueprint
	)
	# # Check if the blueprint is already in the RCC catalog
	$rcc_catalogs = & $RCCExe ht catalogs 2>&1
	#$catalogstring = [string]::Concat($rcc_catalogs)
	$catalogstring = $rcc_catalogs -join "\n"

	if ($catalogstring -match "$blueprint") {
		return $true
	}
 else {
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
	$holotree_spaces = & $RCCExe ht list 2>&1
	$spaces_string = $holotree_spaces -join "\n"
	$agent_match = ($spaces_string -match "rcc.$rcc_ctrl_rmk\s+$rcc_space_rmk_agent\s+$blueprint")
	$output_match = ($spaces_string -match "rcc.$rcc_ctrl_rmk\s+$rcc_space_rmk_output\s+$blueprint")
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
	if ($UseRCC) {
		$blueprint = GetCondaBlueprint $RobotmkRCCdir\conda.yaml		
		debug "> Conda Blueprint: $blueprint"	
		if ( IsRCCEnvReady $blueprint ) {
			debug "RCC environment is ready to use"
			RunTaskRobotmkOutput
			#$output_str = [string]::Concat($output)
			foreach ($line in $output) {
				Write-Host $line 
			}
		}
		else {
			debug "RCC environment is not ready to use. Exiting."	
			#TODO: As long as the RCC env is not ready, we should output something interesting
		}
	}
 else {
		# TODO: finalize native python execution
		Write-Host "TODO: finalize native python execution"
	}
}

function CreateFlagfile {
	param (
		[Parameter(Mandatory = $True)]
		[string]$path
	)  
	$nul > $path
}

function RemoveFlagfile {
	param (
		[Parameter(Mandatory = $True)]
		[string]$path = $null
	)  
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
		debug "> Plugin mode: starting myself again decoupled now..."
		StartRobotmkDecoupled

	}
 elseif ($mode -eq "start") {
		debug "> Direct mode: Trying to start Robotmk... "
		StartRobotmkDaemon
	}
 elseif ($mode -eq "stop") {
		debug "> Direct mode: Trying to kill Robotmk... "
		Write-Host "TODO: kill daemon"
		
	}
 elseif ($mode -eq "restart") {
		# kill daemon
		Write-Host "TODO: kill daemon"
		# start daemon
		Write-Host "TODO: start daemon"
		DaemonController
	}
} 

function StartRobotmkDaemon {
	# Starts the Robotmk process with RCC or native Python
	$blueprint = GetCondaBlueprint $RobotmkRCCdir\conda.yaml		
	debug "> Conda Blueprint: $blueprint"	
	# TODO: How to make RCC execution an optional feature?
	if ($UseRCC) {
		debug "ROBOCORP_HOME = $ROBOCORP_HOME"
		if ( IsRCCEnvReady $blueprint) {
			# if started without "start", we need to detach first
			debug "> RCC environment is ready to use, Daemon can run"
			RunTaskRobotmkAgent
		}
		else {	
			if (IsFlagfileYoungerThanMinutes $Flagfile_RCC_env_creation_in_progress $RCC_env_max_creation_minutes) {
				debug "> Another RCC environment creation is in progress. Exiting."
				return
			}
			else {
				debug "> RCC environment is not ready to use, creating allowed"
				RemoveFlagfile $Flagfile_RCC_env_robotmk_ready
				CreateFlagfile $Flagfile_RCC_env_creation_in_progress
				if (Test-Path ($RobotmkRCCdir + "\hololib.zip")) {
					debug "> hololib.zip found, importing it"
					RCCImportHololib "$RobotmkRCCdir\hololib.zip"
				}
				else {
					debug "> hololib.zip not found, creating catalog from network"		
					# Create a separate Holotree Space for agent and output	
					RCCEnvironmentCreate "$RobotmkRCCdir\robot.yaml" $rcc_ctrl_rmk $rcc_space_rmk_agent
					RCCEnvironmentCreate "$RobotmkRCCdir\robot.yaml" $rcc_ctrl_rmk $rcc_space_rmk_output
				}
				# This takes some minutes... 
				# Watch the progress with `rcc ht list` and `rcc ht catalogs`. First the catalog is created, then
				# both spaces.
				if (CatalogContainsAgentBlueprint $blueprint) {
					CreateFlagfile $Flagfile_RCC_env_robotmk_ready
					RemoveFlagfile $Flagfile_RCC_env_creation_in_progress			
				}
				else {
					debug "> RCC environment creation for Robotmk agent failed for some reason. Exiting."
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

function StartRobotmkDecoupled {
	# Starts the Robotmk process decoupled from the current process
	$powershell = (Get-Command powershell.exe).Path
	DetachProcess $powershell "-File $PSCommandPath start"
	debug "> Exiting... (Daemon will run in background now)"
}

function RunTaskRobotmkAgent {
	# Runs the Robotmk agent
	RCCTaskRun "robotmk-agent" "$RobotmkRCCdir\robot.yaml" $rcc_ctrl_rmk $rcc_space_rmk_agent
}

function RunTaskRobotmkOutput {
	# Runs the Robotmk output
	RCCTaskRun "robotmk-output" "$RobotmkRCCdir\robot.yaml" $rcc_ctrl_rmk $rcc_space_rmk_output
}

function RCCTaskRun {
	# Runs a RCC task with given controller (app) and space (mode)
	param (
		[Parameter(Mandatory = $True)]
		[string]$task,
		[Parameter(Mandatory = $True)]
		[string]$robot_yml,
		[Parameter(Mandatory = $True)]
		[string]$controller,
		[Parameter(Mandatory = $True)]
		[string]$space			
	) 
	# TODO: --silent needed? 
	# TODO: -NoNewWindow needed?
	$Arguments = "task run --controller $controller --space $space -t $task -r $robot_yml"
	debug "Executing: $RCCExe $Arguments"
	$p = Execute-Command -commandTitle "RCC.exe" -commandPath $RCCExe -commandArguments $Arguments
	# $p = Start-Process -Wait -FilePath $RCCExe -ArgumentList $Arguments
	# $stdout = $p.StandardOutput.ReadToEnd()
	# $stderr = $p.StandardError.ReadToEnd()
	$exitCode = $p.ExitCode

}

Function Execute-Command ($commandTitle, $commandPath, $commandArguments) {
	Try {
		$pinfo = New-Object System.Diagnostics.ProcessStartInfo
		$pinfo.FileName = $commandPath
		$pinfo.RedirectStandardError = $true
		$pinfo.RedirectStandardOutput = $true
		$pinfo.UseShellExecute = $false
		$pinfo.Arguments = $commandArguments
		$p = New-Object System.Diagnostics.Process
		$p.StartInfo = $pinfo
		$p.Start() | Out-Null
		[pscustomobject]@{
			commandTitle = $commandTitle
			stdout       = $p.StandardOutput.ReadToEnd()
			stderr       = $p.StandardError.ReadToEnd()
			ExitCode     = $p.ExitCode
		}
		$p.WaitForExit()
	}
	Catch {
		exit
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
	$Arguments = "holotree vars --controller $controller --space $space -r $robot_yml"
	debug "Executing: $RCCExe $Arguments"
	Start-Process -Wait -FilePath $RCCExe -ArgumentList $Arguments
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


# function AgentDaemon {
# 	param (
# 		[Parameter(Mandatory = $True)]
# 		[string]$Binary,
# 		[Parameter(Mandatory = $False)]
# 		[string]$Arguments = $null,
# 		[Parameter(Mandatory = $True)]
# 		[string]$CreationFlags,
# 		[Parameter(Mandatory = $True)]
# 		[string]$ShowWindow,
# 		[Parameter(Mandatory = $True)]
# 		[string]$StartF
# 	)  

# 	# Define all the structures for CreateProcess
# 	Add-Type -TypeDefinition @"
# 	using System;
# 	using System.Diagnostics;
# 	using System.Runtime.InteropServices;
	
# 	[StructLayout(LayoutKind.Sequential)]
# 	public struct PROCESS_INFORMATION
# 	{
# 		public IntPtr hProcess; public IntPtr hThread; public uint dwProcessId; public uint dwThreadId;
# 	}
	
# 	[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
# 	public struct STARTUPINFO
# 	{
# 		public uint cb; public string lpReserved; public string lpDesktop; public string lpTitle;
# 		public uint dwX; public uint dwY; public uint dwXSize; public uint dwYSize; public uint dwXCountChars;
# 		public uint dwYCountChars; public uint dwFillAttribute; public uint dwFlags; public short wShowWindow;
# 		public short cbReserved2; public IntPtr lpReserved2; public IntPtr hStdInput; public IntPtr hStdOutput;
# 		public IntPtr hStdError;
# 	}
	
# 	[StructLayout(LayoutKind.Sequential)]
# 	public struct SECURITY_ATTRIBUTES
# 	{
# 		public int length; public IntPtr lpSecurityDescriptor; public bool bInheritHandle;
# 	}
	
# 	public static class Kernel32
# 	{
# 		[DllImport("kernel32.dll", SetLastError=true)]
# 		public static extern bool CreateProcess(
# 			string lpApplicationName, string lpCommandLine, ref SECURITY_ATTRIBUTES lpProcessAttributes, 
# 			ref SECURITY_ATTRIBUTES lpThreadAttributes, bool bInheritHandles, uint dwCreationFlags, 
# 			IntPtr lpEnvironment, string lpCurrentDirectory, ref STARTUPINFO lpStartupInfo, 
# 			out PROCESS_INFORMATION lpProcessInformation);
# 	}
# "@
	
# 	# StartupInfo Struct
# 	$StartupInfo = New-Object STARTUPINFO
# 	$StartupInfo.dwFlags = $StartF # StartupInfo.dwFlag
# 	$StartupInfo.wShowWindow = $ShowWindow # StartupInfo.ShowWindow
# 	# TODO: Close stdin, stdout, stderr (doesnotwork)
# 	#$StartupInfo.hStdInput = $null 
# 	#$StartupInfo.hStdOutput = [System.Runtime.InteropServices.Marshal]::
# 	#$StartupInfo.hStdError = [System.Runtime.InteropServices.Marshal]::null
# 	$StartupInfo.cb = [System.Runtime.InteropServices.Marshal]::SizeOf($StartupInfo) # Struct Size
	
# 	# ProcessInfo Struct
# 	$ProcessInfo = New-Object PROCESS_INFORMATION
	
# 	# SECURITY_ATTRIBUTES Struct (Process & Thread)
# 	$SecAttr = New-Object SECURITY_ATTRIBUTES
# 	$SecAttr.Length = [System.Runtime.InteropServices.Marshal]::SizeOf($SecAttr)
	
# 	# CreateProcess --> lpCurrentDirectory
# 	$GetCurrentPath = (Get-Item -Path ".\" -Verbose).FullName
	
# 	# TODO: does not work properly - if assigned, process is not created
# 	$DETACHED_PROCESS = 0x00000008 
# 	$CREATE_NEW_PROCESS_GROUP = 0x00000200 
# 	$CREATE_NO_WINDOW = 0x08000000 
# 	# merge creation flags
# 	$CreationFlags = $CreationFlags -bor $DETACHED_PROCESS -bor $CREATE_NEW_PROCESS_GROUP -bor $CREATE_NO_WINDOW
	
# 	# convert to int 
# 	$CreationFlagsInt = [int]$CreationFlags

# 	#	$Binary = $RCCExe
# 	#	$Arguments = "$RCCExe holotree import $RobotmkRCCdir\hololib.zip --silent"	

# 	debug ">>> Executing detached: $Arguments"
# 	# TODO: How to disable black command windows?
# 	#[Kernel32]::CreateProcess($Binary, $Arguments, [ref] $SecAttr, [ref] $SecAttr, $false, $CreationFlagsInt, [IntPtr]::Zero, $GetCurrentPath, [ref] $StartupInfo, [ref] $ProcessInfo) | out-null
# 	#[Kernel32]::CreateProcess($Binary, $Arguments, [ref] $SecAttr, [ref] $SecAttr, $false, $CreationFlagsInt, [IntPtr]::Zero, $GetCurrentPath, [ref] $StartupInfo, [ref] $ProcessInfo) 
# 	[Kernel32]::CreateProcess(
# 		$null, 
# 		$Arguments, 
# 		$null, 
# 		$null, 
# 		$false, 
# 		[CreationFlags]::CREATE_NEW_PROCESS_GROUP -bor [CreationFlags]::DETACHED_PROCESS -bor [CreationFlags]::CREATE_NO_WINDOW, 
# 		$null, 
# 		$GetCurrentPath, 
# 		[ref] $StartupInfo, 
# 		[ref] $ProcessInfo
# 	) 
# 	[System.Runtime.InteropServices.Marshal]::GetLastWin32Error()
# 	$ProcessInfo	
# }

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
	debug ">>> Executing detached: $Binary $Arguments"
	
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
	Write-Host $ProcessInfo.dwProcessId
}

function IsDaemonRunning {
	# Try to read the PID of agent
	$processId = GetDaemonProcess -Cmdline "%robotmk agent start"
	if ( $processId -eq $null) {
		debug ">>> No processes are running"
		if (Test-Path $pidfile) {
			debug ">>> PID file found, removing it"
			Remove-Item $pidfile -Force
		}
		return $false
	}
	else {
		# read PID of daemon
		if (Test-path $pidfile) {
			$DaemonPid = Get-Content $pidfile
			debug ">>> One instance of $DaemonName is already running (PID: $DaemonPid)"
			return $true
		}
		else {
			debug ">>> One instance of $DaemonName is already running, but no PID file found."
			debug ">>> Cleaning up."
			# Instance without PID file
			Stop-Process -Id $processId -Force
			return $false
		}
	}

}

function IsFlagfilePresent {
	param (
		[Parameter(Mandatory = $True)]
		[string]$flagfile
	)  	
	if (Test-Path $flagfile) {
		debug ">>> Flagfile $flagfile found"
		return $true
	}
	else {
		return $false
	}
}


function GetDaemonProcess {
	param (
		[Parameter(Mandatory = $True)]
		[string]$Cmdline
	)
	$processId = Get-WmiObject -Query "SELECT * FROM Win32_Process WHERE CommandLine like '$Cmdline'" | Select ProcessId
	#debug ">>> ProcessId: $processId"
	return $processId.processId

}


main