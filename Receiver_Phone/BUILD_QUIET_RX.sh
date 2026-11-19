#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
python3 - <<'PY'
from pathlib import Path
import shutil
root=Path.cwd();source=root.parent/'Radio_Source/receiver/gr-ieee802-11';target=root/'rx_runtime/source'
if not target.exists():shutil.copytree(source,target,ignore=shutil.ignore_patterns('build','.git','__pycache__','*.pyc'))
for p in target.rglob('*'):
 if p.is_file():
  b=p.read_bytes()
  if b'\r\n' in b and b'\0' not in b:
   try:b.decode('utf-8')
   except UnicodeDecodeError:continue
   p.write_bytes(b.replace(b'\r\n',b'\n'))
p=target/'lib/parse_mac.cc';text=p.read_text();first='      std::cout << "\\n========== Metadata ==========\\n";';last='      std::cout << "==============================\\n";'
if '// FYP: honor the existing logging flags' not in text:
 assert first in text and last in text
 text=text.replace(first,'      // FYP: honor the existing logging flags\n      if (d_log || d_debug) {\n'+first).replace(last,last+'\n      }');p.write_text(text)
p=target/'lib/decode_mac.cc';text=p.read_text()
if '// FYP diagnostic counters' not in text:
 text=text.replace('#include <iomanip>','#include <iomanip>\n#include <chrono>')
 text=text.replace('message_port_register_out(pmt::mp("out"));','message_port_register_out(pmt::mp("out"));\n        message_port_register_out(pmt::mp("rx_stats"));')
 block="""// FYP diagnostic counters; CRC acceptance and payload are unchanged.
        const bool bad_crc = result.checksum() != 558161692;
        ++d_checked;
        d_bad_crc += bad_crc;
        const auto now = std::chrono::steady_clock::now();
        if (now - d_last_stats >= std::chrono::seconds(1)) {
            auto stats = pmt::make_dict();
            stats = pmt::dict_add(stats, pmt::mp("checked"), pmt::from_uint64(d_checked));
            stats = pmt::dict_add(stats, pmt::mp("bad_crc"), pmt::from_uint64(d_bad_crc));
            message_port_pub(pmt::mp("rx_stats"), stats);
            d_last_stats = now;
        }
        if (bad_crc) {"""
 text=text.replace('if (result.checksum() != 558161692) {',block)
 text=text.replace('    bool d_debug;','    uint64_t d_checked = 0;\n    uint64_t d_bad_crc = 0;\n    std::chrono::steady_clock::time_point d_last_stats{};\n    bool d_debug;')
 p.write_text(text)
print('Private receiver prepared: debug print control and diagnostic counters; CRC acceptance unchanged.')
PY
FYP_RX_DIR="$PWD/rx_runtime"
# Apply capture-only changes to both existing and freshly copied runtime sources.
if patch --batch --forward --dry-run -s -p1 -d "$FYP_RX_DIR/source" < "$FYP_RX_DIR/capture-io.patch" >/dev/null; then
  patch --batch --forward -p1 -d "$FYP_RX_DIR/source" < "$FYP_RX_DIR/capture-io.patch"
else
  patch --batch --reverse --dry-run -s -p1 -d "$FYP_RX_DIR/source" < "$FYP_RX_DIR/capture-io.patch"
fi
cmake_cache="$FYP_RX_DIR/build/CMakeCache.txt"
fresh=()
if [[ -f "$cmake_cache" ]] && ! grep -Fxq "CMAKE_HOME_DIRECTORY:INTERNAL=$FYP_RX_DIR/source" "$cmake_cache"; then
  fresh=(--fresh)
fi
cmake "${fresh[@]}" -S "$FYP_RX_DIR/source" -B "$FYP_RX_DIR/build" \
 -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
 -DCMAKE_INSTALL_PREFIX="$FYP_RX_DIR/install" -DGR_PYTHON_DIR="$FYP_RX_DIR/install/python" \
 -DPYTHON_EXECUTABLE=/usr/bin/python3 -DPython_EXECUTABLE=/usr/bin/python3 \
 -DGnuradio_DIR=/usr/lib/cmake/gnuradio -Dpybind11_DIR=/usr/lib/cmake/pybind11 \
 -DENABLE_PYTHON=ON -DENABLE_DOXYGEN=OFF
cmake --build "$FYP_RX_DIR/build" --parallel 2
cmake --install "$FYP_RX_DIR/build"
PYTHONPATH="$FYP_RX_DIR/install/python" LD_LIBRARY_PATH="$FYP_RX_DIR/install/lib:$FYP_RX_DIR/install/lib64" \
 /usr/bin/python3 -c 'import ieee802_11; assert hasattr(ieee802_11.extract_csi,"set_channel"); print("Private RX imports and channel setter verified:",ieee802_11.__file__)'
/usr/bin/python3 - <<'PY'
from pathlib import Path
import hashlib
import json

runtime = Path('rx_runtime')
install = runtime / 'install'
libraries = {
    path.resolve().relative_to(runtime.resolve())
    for pattern in (
        'lib*/libgnuradio-ieee802_11.so',
        'python/ieee802_11/ieee802_11_python.*.so',
    )
    for path in install.glob(pattern)
}
files = [Path('capture-io.patch'), *sorted(libraries)]
receipt = {
    'capture_io_version': 1,
    'sha256': {str(path): hashlib.sha256((runtime / path).read_bytes()).hexdigest()
               for path in files},
}
temporary = runtime / 'ready.json.tmp'
temporary.write_text(json.dumps(receipt, indent=2) + '\n')
temporary.replace(runtime / 'ready.json')
PY
