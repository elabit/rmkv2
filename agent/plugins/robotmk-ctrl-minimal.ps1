
$scriptname_noext = (Get-Item -Path $MyInvocation.MyCommand.Path).BaseName
$scriptname = (Get-Item -Path $MyInvocation.MyCommand.Path).PSChildName
# read mode from args or set to 0
$MODE = if ($args[0]) { $args[0] } else { $nul };
$PPID = if ($args[1]) { $args[1] } else { $nul };

# $DEBUG = $true
# #$DEBUG = $false


# $UseRCC = $true



# # Execution phase: 
# # 1 = started by Agent, with parent process
# # 2 = started by itself detached, without parent process
# $EXEC_PHASE = "-"


function main() {
	# # robotmk.ps1 : start Robotmk to produce output
	# # robotmk-ctrl.ps1 : start Robotmk to control the daemon
	# SetScriptVars
	
	# Ensure-Directory $RMKlogdir
	# Ensure-Directory $RMKTmpDir
	# Ensure-Directory $ROBOCORP_HOME
	# Ensure-Directory $PDataRMKPlugins
	# LogConfig
	

	StartAgentController($MODE)
		
}




function StartAgentController {
	param (
		[Parameter(Mandatory = $False)]
		[string]$mode = $null
	)  

	if ($mode -eq "") {
		StartControllerDecoupled

	}
 elseif ($mode -eq "start") {
		while ($true) {
			Start-Sleep -s 10
		}
	}
} 


function StartControllerDecoupled {
	try {
		#LogDebug "Copy myself ($scriptname) to Robotmk plugin directory $PDataRMKPlugins."
		Copy-Item $PSCommandPath $PDataRMKPlugins -Force -ErrorAction SilentlyContinue
	}
	catch {
		#LogError "Could not copy myself ($scriptname) to Robotmk plugin directory $PDataRMKPlugins. Exiting."
		return
	}
	$RobotmkControllerPS = "$PDataRMKPlugins\$scriptname"
	$powershell = (Get-Command powershell.exe).Path
	DetachProcess $powershell "-File $RobotmkControllerPS start ${PID}"
	# Exiting now
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

	# Versuch 
	$CREATE_NEW_CONSOLE = 0x00000010

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
}


#   _          _                 
#  | |        | |                
#  | |__   ___| |_ __   ___ _ __ 
#  | '_ \ / _ \ | '_ \ / _ \ '__|
#  | | | |  __/ | |_) |  __/ |   
#  |_| |_|\___|_| .__/ \___|_|   
#               | |              
#               |_|              


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



function SetScriptVars {
	# TODO: Set RObocorp Home with robotmk.yaml
	# Programdata var
	$PData = [System.Environment]::GetFolderPath("CommonApplicationData")
	$Global:PDataCMK = "$PData\checkmk"
	$Global:PDataCMKAgent = "$PDataCMK\agent"
	# Set to tmp dir for testing
	$Global:PDataRMKPlugins = "C:\tmp\robotmk\agent"
	#$Global:PDataRMKPlugins = "${PData}\robotmk\plugins"

	# Try to read the environment variables from the agent. If not set, use defaults.
	$Global:MK_LOGDIR = "$PDataCMKAgent\log"
	$Global:RMKLogDir = "$MK_LOGDIR\robotmk"
	$Global:MK_TEMPDIR = "$PDataCMKAgent\tmp"
	$Global:RMKTmpDir = "$MK_TEMPDIR\robotmk"
	$Global:MK_CONFDIR = "$PDataCMKAgent\config"
	$Global:RMKCfgDir = "$MK_CONFDIR\robotmk"
	$Global:RMKLogfile = "$RMKLogDir\${scriptname_noext}-plugin.log"	

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


main