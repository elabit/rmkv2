
# Credits to https://github.com/FuzzySecurity/PowerShell-Suite/blob/master/Invoke-CreateProcess.ps1

# - Determine if daemon is running
#   - read pidfile
#   - check if process is running
# - If not running, start daemon

$PyName = "python"
$PyExe = "C:\Python310\python.exe"
$DaemonName = "daemon.py"
# TODO: Determine Agent dir
#$CMKAgentDir = "C:\ProgramData\check_mk\agent"
$CMKAgentDir = "C:\Users\vagrant\Documents\01_dev\rmkv2\agent"
$RCCExe = $CMKAgentDir + "\bin\rcc.exe"
$RobotmkRCCdir = $CMKAgentDir + "\lib\rcc_robotmk"
$CMKtempdir = $CMKAgentDir + "\tmp"


function IsRCCEnvReady {
	# TODO: Blueprint check not working
	
	# # Get the blueprint hash for conda.yaml
	# $condahash = & $RCCExe ht hash $RobotmkRobotdir\conda.yaml 2>&1
	# $condahash -match "Blueprint hash for.*is (?<blueprint>[A-Za-z0-9]*)\."
	# $blueprint = $Matches.blueprint
	
	# # Check if the blueprint is already in the RCC catalog
	# $rcc_catalogs = & $RCCExe ht catalogs -j | ConvertFrom-Json
	# $catalog = $rcc_catalogs | Where-Object { $_.blueprint -eq "dc9a047d0b412ec3" }
	
	# FIXME: Only for debugging
	$catalog = $false
	if ($catalog -eq $true) {
		return $true
	}
	else {
		return $false
	}
}

function main() {
	# Red pidfile from tmp dir
	$pidfile = "C:\Users\vagrant\AppData\Local\Temp\daemon.py.pid"
	$daemon_pid = IsDaemonRunning -PyName $PyName -DaemonName $DaemonName
	if (-Not ($daemon_pid)) {
		# delete pidfile if exists
		if (Test-Path $pidfile) {
			Remove-Item $pidfile
		}
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
	
	# TODO: 
	# - Check if RCC is desired: 
	#   - if no, start Python process natively without RCC	
	#   - if yes, loop: check if RCC environment is ready to use
	#  		- if no, create RCC environment
	#       - if yes, start Python process with RCC
	#   -  
	# Call CreateProcess

	# check if state file is present
	if (Test-Path ($CMKtempdir + "\rcc_env_in_creation")) {
		Write-Host "RCC environment creation in progress, exiting script"
		return
	}
	else {
		if (IsRCCEnvReady -eq $True) {
			Write-Host "RCC environment is ready to use"
			# delete state file
			Remove-Item ($CMKtempdir + "\rcc_env_in_creation") -Force -ErrorAction SilentlyContinue
			# start python daemon
			$Binary = $PyExe
			# FIXME: start daemon in RCC!
			$Arguments = "$PyExe daemon.py start"
		}
		else {
			Write-Host "RCC environment is not ready to use, creating it"
			# TODO: ENABLE THIS LATER
			New-Item -ItemType File -Path ($CMKtempdir + "\rcc_env_in_creation") -Force			
			if (Test-Path ($RobotmkRCCdir + "\hololib.zip")) {
				Write-Host "> hololib.zip found, importing it"
				$Binary = $RCCExe
				$Arguments = "$RCCExe holotree import $RobotmkRCCdir\hololib.zip --silent"
			}
			else {
				Write-Host "> hololib.zip not found, creating catalog from network"				
				$Binary = $RCCExe
				# Start RCC to create the env
				$Arguments = "$RCCExe holotree vars -r $RobotmkRCCdir\robot.yaml --silent"
			}
		}		
	}
	Write-host ">>> Executing detached: $Arguments"
	# TODO: How to disable black cms windows? 
	[Kernel32]::CreateProcess($Binary, $Arguments, [ref] $SecAttr, [ref] $SecAttr, $false, $CreationFlagsInt, [IntPtr]::Zero, $GetCurrentPath, [ref] $StartupInfo, [ref] $ProcessInfo) | out-null
	#[System.Runtime.InteropServices.Marshal]::GetLastWin32Error()
}

function IsDaemonRunning {
	param (
		[Parameter(Mandatory = $true)][string]$PyName,
		[Parameter(Mandatory = $true)][string]$DaemonName
	)
	$processes = Get-CimInstance Win32_Process -Filter "name='python.exe'" -ErrorAction SilentlyContinue
	if ($processes) {
		foreach ($process in $processes) {
			if ($process.CommandLine -match $DaemonName) {
				return $process.ProcessId
			}
		}
	}
	return 0
}

main