# Sourced internally by build/start scripts. No system-wide module installation.
FYP_TX_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$FYP_TX_ROOT/install/python:$FYP_TX_ROOT/generated${PYTHONPATH:+:$PYTHONPATH}"
export LD_LIBRARY_PATH="$FYP_TX_ROOT/install/lib:$FYP_TX_ROOT/install/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export GRC_HIER_PATH="$FYP_TX_ROOT/generated"
