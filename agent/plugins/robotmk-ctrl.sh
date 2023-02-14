#!/bin/bash

SCRIPTNAME=$(basename "$0")
SCRIPTNAME_NOEXT="${SCRIPTNAME%.*}"

# read arg1 or set default
MODE=${1:-"(none)"}

DEBUG=1
USE_RCC=1

function main() {
    set_script_vars
    ensure_dir "$ROBOTMK_LOGDIR"
    # TODO: whicih dirs to ensure?
    log_config

    # if scriptname is not robotmk-ctrl.sh, exit
    if [[ "$SCRIPTNAME_NOEXT" =~ "robotmk$" ]]; then
        produce_agent_output
    elif [[ "$SCRIPTNAME_NOEXT" =~ "robotmk-ctrl$" ]]; then

        start_agent_controller $MODE
    else
        log_error "Script name '$SCRIPTNAME_NOEXT' cannot be evaluated. Exiting."
    fi

}

function produce_agent_output() {
    log_debug "To be implemented!"
}

function start_agent_controller() {
	# mode=start/stop/restart
	# CAVEAT: using the Daemon control words (start/stop etc) will start the Daemon in the 
	# user context. This is not what we probably want. The Daemon should better in the system context.
    mode=$1
    touch "$CONTROLLER_DEADMAN_FILE"
    if [[ "$mode" == "(none)" ]]; then
        log_info "---- Script was started without mode (by Agent?); have to start myself again to damonize."
        start_agent_controller_decoupled
    elif [[ "$mode" == "start"]]
    
    fi
}

function double_fork() {
    pid=0
    # FORK 1: detach process from terminal
    pid=$(fork)

    #shellcheck disable=SC2086
    if [ $pid -ne 0 ]; then
        # Terminate parent process
        exit 0
    fi

    # Create a new session to run as daemon
    setsid

    # FORK 2: prevent reattaching to terminal
    pid=$(fork)

    #shellcheck disable=SC2086
    if [ $pid -ne 0 ]; then
        # Terminate parent process
        exit 0
    fi

    # Write PID to file for reference
    echo $$ > /var/run/daemon.pid

    # Redirect standard input/output to /dev/null
    exec 0<&-
    exec 1>&-
    exec 2>&-
}


function start_agent_controller_decoupled() {
	# Starts the Robotmk process decoupled from the current process
	# Hand over the PID of calling process and log it

	try {
		LogDebug "Copy myself ($scriptname
	) to Robotmk plugin directory $PDataRMKPlugins."
		Copy-Item $PSCommandPath $PDataRMKPlugins -Force -ErrorAction SilentlyContinue
	}
	catch {
		LogError "Could not copy myself ($scriptname
	) to Robotmk plugin directory $PDataRMKPlugins. Exiting."
		return
	}
	$RobotmkControllerPS = "$PDataRMKPlugins\$scriptname"
	$powershell = (Get-Command powershell.exe).Path
	DetachProcess $powershell "-File $RobotmkControllerPS start ${PID}"
	LogInfo "Exiting... (Daemon will run in background now)"
	# sleep  100 seconds to give the daemon some time to start
	# Start-Sleep -s 100
    
}

#   _____   _____ _____   _          _
#  |  __ \ / ____/ ____| | |        | |
#  | |__) | |   | |      | |__   ___| |_ __   ___ _ __
#  |  _  /| |   | |      | '_ \ / _ \ | '_ \ / _ \ '__|
#  | | \ \| |___| |____  | | | |  __/ | |_) |  __/ |
#  |_|  \_\\_____\_____| |_| |_|\___|_| .__/ \___|_|
#                                     | |
#                                     |_|

function is_rcc_env_ready() {
    # check if RCC env is ready
    # return 0 if ready, 1 if not
    log_debug "To be implemented!"
}

function get_conda_blueprint() {
    # get conda blueprint
    # return 0 if ready, 1 if not
    log_debug "To be implemented!"
}

function rcc_import_hololib() {
    # import hololib
    # return 0 if ready, 1 if not
    log_debug "To be implemented!"
}

function ensure_rcc_present() {
    # ensure rcc is present
    # return 0 if ready, 1 if not
    log_debug "To be implemented!"
}

#   _          _
#  | |        | |
#  | |__   ___| |_ __   ___ _ __
#  | '_ \ / _ \ | '_ \ / _ \ '__|
#  | | | |  __/ | |_) |  __/ |
#  |_| |_|\___|_| .__/ \___|_|
#               | |
#               |_|

check_vars() {
    var_names=("$@")
    for var_name in "${var_names[@]}"; do
        [ -z "${!var_name}" ] && echo "$var_name is unset." && var_unset=true
    done
    [ -n "$var_unset" ] && exit 1
    return 0
}

function set_script_vars() {
    # TODO: Set RObocorp Home with robotmk.yaml

    # exit if no mode is set
    # Usage for this case
    check_vars MK_LOGDIR MK_CONFDIR MK_LIBDIR MK_VARDIR
    PLUGINSDIR="$MK_LIBDIR/plugins"
    ROBOTMK_LOGDIR="$MK_LOGDIR/robotmk"
    ROBOTMK_CONFDIR="$MK_CONFDIR/robotmk"
    ROBOTMK_LIBDIR="$MK_LIBDIR/robotmk"
    ROBOTMK_VARDIR="$MK_VARDIR/robotmk"
    export_vars RMK_LOGDIR ROBOTMK_CONFDIR ROBOTMK_LIBDIR ROBOTMK_VARDIR PLUGINSDIR

    RMK_LOGFILE="$ROBOTMK_LOGDIR/${SCRIPTNAME_NOEXT}.log"

    # TODO: Deploy with Bakery
    RCCBIN="/home/simonmeggle/bin/rcc"
    # Ref 7e8b2c1 (agent.py)
    AGENT_PIDFILE="${ROBOTMK_VARDIR}/robotmk_agent.pid"
    # Ref 23ff2d1 (agent.py)
    CONTROLLER_DEADMAN_FILE="${ROBOTMK_VARDIR}/robotmk_controller_deadman_file"
    # This flagfile indicates that both there is a usable holotree space for "robotmk agent/output"
    ROBOTMK_AGENT_LASTEXITCODE="${ROBOTMK_VARDIR}/robotmk_agent_lastexitcode"
    # IMPORTANT! All other Robot subprocesses must respect this file and not start if it is present!
    # (There is only ONE RCC creation allowed at a time.)
    FLAGFILE_RCC_ENV_CREATION_IN_PROGRESS="${ROBOTMK_VARDIR}/rcc_env_creation_in_progress.lock"
    # how many minutes to wait for a/any single RCC env creation to be finished (maxage of $Flagfile_RCC_env_creation_in_progress)
    RCC_ENV_MAX_CREATION_MINUTES=1

    # RCC namespaces
    # - controller
    RCC_CTRL_RMK="robotmk"
    # - space for agent and output
    RCC_SPACE_RMK_AGENT="agent"
    RCC_SPACE_RMK_OUTPUT="output"
}

function log() {
    echo "$1" | tee -a "$RMK_LOGFILE"
}

function log_info() {
    log "INFO: $1"
}

function log_debug() {
    [ "$DEBUG" -eq 1 ] && log "$1"
}

function log_error() {
    log "ERROR: $1"
}

function log_config() {
    log_debug "--- 8< --------------------"
    log_debug "CONFIGURATION:"
    log_debug "- scriptname_noext: $SCRIPTNAME_NOEXT"
    log_debug "- mode: $MODE"
    log_debug "- PID: $$"
    log_debug "- PPID: $PPID"
    log_debug "- ROBOTMK_LOGDIR: $ROBOTMK_LOGDIR"
    log_debug "- ROBOTMK_CONFDIR: $ROBOTMK_CONFDIR"
    log_debug "- ROBOTMK_LIBDIR: $ROBOTMK_LIBDIR"
    log_debug "- ROBOTMK_VARDIR: $ROBOTMK_VARDIR"
    log_debug "- Use RCC: $USE_RCC"
    if [ "$USE_RCC" -eq 1 ]; then
        log_rcc_config
    fi
    log_debug "-------------------- >8 ---"
}

function log_rcc_config() {
    log_debug "RCC CONFIGURATION:"
    log_debug "- ROBOCORP_HOME: $ROBOCORP_HOME"
    log_debug "- RCCBIN: $RCCBIN"
    log_debug "- Robotmk RCC holotree spaces:"
    log_debug "  - Robotmk agent: rcc.${RCC_CTRL_RMK}/${RCC_SPACE_RMK_AGENT}"
    log_debug "  - Robotmk output: rcc.${RCC_CTRL_RMK}/${RCC_SPACE_RMK_OUTPUT}"
}

function ensure_dir() {
    # ensure that a directory exists
    # usage: ensure_directory <directory>
    local directory="$1"
    if [ ! -d "$directory" ]; then
        mkdir -p "$directory"
    fi
}

function export_vars() {
    # export all vars given as args
    var_names=("$@")
    for var_name in "${var_names[@]}"; do
        export "$var_name"
    done
}

main "$@"
