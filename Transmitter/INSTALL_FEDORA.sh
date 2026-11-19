#!/usr/bin/env bash
set -euo pipefail
if ! command -v dnf >/dev/null; then
    echo 'This installer is for Fedora. No package changes made.' >&2
    exit 1
fi
sudo dnf install -y \
    gnuradio gnuradio-devel python3-gnuradio \
    uhd uhd-devel uhd-tools uhd-firmware \
    cmake gcc gcc-c++ make git unzip \
    python3-devel python3-numpy python3-qt5 \
    python3-pybind11 pybind11-devel python3-packaging \
    boost-devel volk-devel fftw-devel spdlog-devel fmt-devel
/usr/bin/python3 -c 'from gnuradio import gr, uhd, qtgui; from PyQt5 import Qt; print("GNU Radio:", gr.version())'
echo 'Dependencies installed. Next: bash BUILD.sh'
