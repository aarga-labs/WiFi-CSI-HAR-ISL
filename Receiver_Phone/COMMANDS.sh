# Source this from the collector folder in BOTH run terminals:
#   source ./COMMANDS.sh P04 S01
# This only defines commands. It does not start any recording.
if [[ ! -f "$PWD/run_block.py" || ! -f "$PWD/START_CSI_RX.sh" ]]; then
    echo 'First cd to the Capture_Pipeline/Receiver_Phone folder, then source COMMANDS.sh.'
    return 1
fi
case "${1:-P04}" in P00|P04|P05) ;; *) echo 'Use P00, P04, or P05.'; return 1 ;; esac
case "${2:-S01}" in S[0-9][0-9]) ;; *) echo 'Use a session such as S01 or S02.'; return 1 ;; esac
export FYP_COMMANDS_DIR="$PWD"
export FYP_PARTICIPANT="${1:-P04}"
export FYP_SESSION="${2:-S01}"
export FYP_SHUFFLE_SEED="$((10#${FYP_PARTICIPANT#P} * 100 + 10#${FYP_SESSION#S}))"
phone() {
    /usr/bin/python3 "$FYP_COMMANDS_DIR/run_block.py" --pid "$FYP_PARTICIPANT" --session "$FYP_SESSION" "$@"
}
csi() {
    "$FYP_COMMANDS_DIR/START_CSI_RX.sh" --pid "$FYP_PARTICIPANT" --session "$FYP_SESSION" --addr 192.168.10.7 --block "$@"
}
echo "Commands ready: $FYP_PARTICIPANT / $FYP_SESSION. Use p04_stand_still / p05_stand_still, then the next named run. Each starts CSI + phone."
paired_run() {
    /usr/bin/python3 "$FYP_COMMANDS_DIR/run_paired.py" --session "$FYP_SESSION" "$@"
}
p04_stand_still() { paired_run --pid P04 --block stand_still "$@"; }
p04_sit_still() { paired_run --pid P04 --block sit_still "$@"; }
p04_activities_stand() { paired_run --pid P04 --block activities_standing "$@"; }
p04_activities_stand_patch() { paired_run --pid P04 --block activities_standing_makeup "$@"; }
p04_activities_sit() { paired_run --pid P04 --block activities_seated "$@"; }
p04_sign_stand() { paired_run --pid P04 --block signs_standing "$@"; }
p04_sign_sit() { paired_run --pid P04 --block signs_seated "$@"; }
p04_mixed_activity() { paired_run --pid P04 --block mixed_activity "$@"; }
p05_stand_still() { paired_run --pid P05 --block stand_still "$@"; }
p05_sit_still() { paired_run --pid P05 --block sit_still "$@"; }
p05_activities_stand() { paired_run --pid P05 --block activities_standing "$@"; }
p05_activities_sit() { paired_run --pid P05 --block activities_seated "$@"; }
p05_sign_stand() { paired_run --pid P05 --block signs_standing "$@"; }
p05_sign_sit() { paired_run --pid P05 --block signs_seated "$@"; }
p05_mixed_activity() { paired_run --pid P05 --block mixed_activity "$@"; }
