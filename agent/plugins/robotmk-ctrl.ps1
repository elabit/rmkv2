
# Credits to https://github.com/FuzzySecurity/PowerShell-Suite/blob/master/Invoke-CreateProcess.ps1

# - Determine if daemon is running
#   - read pidfile
#   - check if process is running
# - If not running, start daemon

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
# TODO: How to set system env vars globally? Needed?
[System.Environment]::SetEnvironmentVariable('ROBOCORP_HOME', 'C:\rcc')


function IsRCCEnvReady {
	# # Get the blueprint hash for conda.yaml
	$condahash = & $RCCExe ht hash $RobotmkRCCdir\conda.yaml 2>&1
	$condahash -match "Blueprint hash for.*is (?<blueprint>[A-Za-z0-9]*)\."
	$blueprint = $Matches.blueprint
	
	# # Check if the blueprint is already in the RCC catalog
	$rcc_catalogs = & $RCCExe ht catalogs 2>&1
	$catalogstring = [string]::Concat($rcc_catalogs)
	if ($catalogstring -match "$blueprint") {
		return $true
	}
	else {
		return $false
	}
}

function main() {
	
	$daemon_pid = IsDaemonRunning
	if (-Not ($daemon_pid)) {
		Write-Host "Starting the Daemon"
		StartDaemon -Binary $PyExe -Arguments "$PyExe daemon.py start" -CreationFlags 0x00000000 -ShowWindow 0x0001 -StartF 0x1 
	}
	else {
		Write-Host "Daemon is already running with PID: $daemon_pid"
	}
}

function StartDaemon {
	param (
		[Parameter(Mandatory = $True)]
		[string]$Binary,
		[Parameter(Mandatory = $False)]
		[string]$Arguments = $null,
		[Parameter(Mandatory = $True)]
		[string]$CreationFlags,
		[Parameter(Mandatory = $True)]
		[string]$ShowWindow,
		[Parameter(Mandatory = $True)]
		[string]$StartF
	)  

	# Define all the structures for CreateProcess
	Add-Type -TypeDefinition @"
	using System;
	using System.Diagnostics;
	using System.Runtime.InteropServices;
	
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
	$StartupInfo.dwFlags = $StartF # StartupInfo.dwFlag
	$StartupInfo.wShowWindow = $ShowWindow # StartupInfo.ShowWindow
	# TODO: Close stdin, stdout, stderr (doesnotwork)
	#$StartupInfo.hStdInput = $null 
	#$StartupInfo.hStdOutput = [System.Runtime.InteropServices.Marshal]::
	#$StartupInfo.hStdError = [System.Runtime.InteropServices.Marshal]::null
	$StartupInfo.cb = [System.Runtime.InteropServices.Marshal]::SizeOf($StartupInfo) # Struct Size
	
	# ProcessInfo Struct
	$ProcessInfo = New-Object PROCESS_INFORMATION
	
	# SECURITY_ATTRIBUTES Struct (Process & Thread)
	$SecAttr = New-Object SECURITY_ATTRIBUTES
	$SecAttr.Length = [System.Runtime.InteropServices.Marshal]::SizeOf($SecAttr)
	
	# CreateProcess --> lpCurrentDirectory
	$GetCurrentPath = (Get-Item -Path ".\" -Verbose).FullName
	
	# TODO: does not work properly - if assigned, process is not created
	$DETACHED_PROCESS = 0x00000008 
	$CREATE_NEW_PROCESS_GROUP = 0x00000200 
	$CREATE_NO_WINDOW = 0x08000000 
	# merge creation flags
	$CreationFlags = $CreationFlags -bor $DETACHED_PROCESS -bor $CREATE_NEW_PROCESS_GROUP -bor $CREATE_NO_WINDOW
	
	# convert to int 
	$CreationFlagsInt = [int]$CreationFlags
	
	# TODO: How to make RCC execution an optional feature?
	if ($UseRCC) {
		# check if state file is present
		if (Test-Path ($CMKtempdir + "\rcc_env_in_creation")) {
			Write-Host "RCC environment creation in progress, exiting script"
			return
		}
		else {
			if ( IsRCCEnvReady ) {
				Write-Host "RCC environment is ready to use"
				# delete state file
				Remove-Item ($CMKtempdir + "\robotmk_rcc_env_in_creation") -Force -ErrorAction SilentlyContinue
				$Binary = $RCCExe
				$Arguments = "$RCCExe task run -t robotmk-agent -r $RobotmkRCCdir\robot.yaml --silent"			
			}
			else {
				Write-Host "RCC environment is not ready to use, creating it"
				# create state file 
				New-Item -ItemType File -Path ($CMKtempdir + "\robotmk_rcc_env_in_creation") -Force			
				if (Test-Path ($RobotmkRCCdir + "\hololib.zip")) {
					Write-Host "> hololib.zip found, importing it"
					$Binary = $RCCExe
					$Arguments = "$RCCExe holotree import $RobotmkRCCdir\hololib.zip --silent"
				}
				else {
					Write-Host "> hololib.zip not found, creating catalog from network"				
					$Binary = $RCCExe
					# Start RCC to create the env
					# TODO: capture log output
					$Arguments = "$RCCExe holotree vars -r $RobotmkRCCdir\robot.yaml"
				}
			}		
		}
	}
 else {
		# TODO: finalize native python execution
		$Binary = $PythonExe
		$Arguments = "$PythonExe $RobotmkAgent"
	}

	Write-host ">>> Executing detached: $Arguments"
	# TODO: How to disable black command windows?
	#[Kernel32]::CreateProcess($Binary, $Arguments, [ref] $SecAttr, [ref] $SecAttr, $false, $CreationFlagsInt, [IntPtr]::Zero, $GetCurrentPath, [ref] $StartupInfo, [ref] $ProcessInfo) | out-null
	[Kernel32]::CreateProcess($Binary, $Arguments, [ref] $SecAttr, [ref] $SecAttr, $false, $CreationFlagsInt, [IntPtr]::Zero, $GetCurrentPath, [ref] $StartupInfo, [ref] $ProcessInfo) 
}




function IsDaemonRunning {
	# Try to read the PID of agent
	$processId = GetDaemonProcess -Cmdline "%python.exe -m robotmk agent start"
	if ( $processId -eq $null) {
		Write-Host ">>> No processes are running"
		if (Test-Path $pidfile) {
			Write-Host ">>> PID file found, removing it"
			Remove-Item $pidfile -Force
		}
		return $false
	}
 else {
		# read PID of daemon
		if (Test-path $pidfile) {
			$DaemonPid = Get-Content $pidfile
			Write-Host ">>> One instance of $DaemonName is already running (PID: $DaemonPid)"
			return $true
		}
		else {
			Write-Host ">>> One instance of $DaemonName is already running, but no PID file found."
			Write-Host ">>> Cleaning up."
			# Instance without PID file
			Stop-Process -Id $processId -Force
			return $false
		}
	}

}


function GetDaemonProcess {
	param (
		[Parameter(Mandatory = $True)]
		[string]$Cmdline
	)
	$processId = Get-WmiObject -Query "SELECT * FROM Win32_Process WHERE CommandLine like '$Cmdline'" | Select ProcessId
	Write-Host ">>> ProcessId: $processId"
	return $processId.processId

}

main