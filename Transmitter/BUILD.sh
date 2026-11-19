#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
source ./ENV.sh
/usr/bin/python3 -c 'from gnuradio import gr; from PyQt5 import Qt; import numpy, pybind11; assert gr.version().startswith("3.10."), "Use GNU Radio 3.10.x"; print("Building for GNU Radio", gr.version())'
mkdir -p build install generated
# Two jobs by default limits memory pressure on a fresh laptop.
FYP_BUILD_JOBS="${FYP_BUILD_JOBS:-2}"
FYP_CMAKE_ARGS=()
for config in /usr/lib64/cmake/gnuradio /usr/lib/cmake/gnuradio; do
    if [[ -f "$config/GnuradioConfig.cmake" ]]; then
        FYP_CMAKE_ARGS+=("-DGnuradio_DIR=$config"); break
    fi
done
for config in /usr/share/cmake/pybind11 /usr/lib64/cmake/pybind11 /usr/lib/cmake/pybind11; do
    if [[ -f "$config/pybind11Config.cmake" ]]; then
        FYP_CMAKE_ARGS+=("-Dpybind11_DIR=$config"); break
    fi
done
for module in gr-foo gr-ieee802-11; do
    cache="$FYP_TX_ROOT/build/$module/CMakeCache.txt"
    fresh=()
    if [[ -f "$cache" ]] && ! grep -Fxq "CMAKE_HOME_DIRECTORY:INTERNAL=$FYP_TX_ROOT/source/$module" "$cache"; then
        fresh=(--fresh)
    fi
    cmake "${fresh[@]}" -S "$FYP_TX_ROOT/source/$module" -B "$FYP_TX_ROOT/build/$module" \
        -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
        -DCMAKE_INSTALL_PREFIX="$FYP_TX_ROOT/install" \
        -DGR_PYTHON_DIR="$FYP_TX_ROOT/install/python" \
        -DPYTHON_EXECUTABLE=/usr/bin/python3 -DPython_EXECUTABLE=/usr/bin/python3 \
        -DPython3_EXECUTABLE=/usr/bin/python3 -DENABLE_PYTHON=ON -DENABLE_DOXYGEN=OFF \
        "${FYP_CMAKE_ARGS[@]}"
    cmake --build "$FYP_TX_ROOT/build/$module" --parallel "$FYP_BUILD_JOBS"
    cmake --install "$FYP_TX_ROOT/build/$module"
done
grcc "$FYP_TX_ROOT/source/gr-ieee802-11/examples/wifi_phy_hier.grc" -o "$FYP_TX_ROOT/generated"
/usr/bin/python3 "$FYP_TX_ROOT/check_setup.py"
/usr/bin/python3 -c 'import json,sys,sysconfig; from pathlib import Path; from gnuradio import gr; Path("build/BUILD_OK.json").write_text(json.dumps({"python":sys.version,"soabi":sysconfig.get_config_var("SOABI"),"gnuradio":gr.version()},indent=2)+"\n")'
echo 'BUILD PASSED. Next: bash SETUP_NETWORK.sh, then bash START_STABLE_TX.sh --gain 30'
