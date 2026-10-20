# ESP32-CSI-Tool: Fall Detection Documentation

This document provides a clear, high-level explanation of the ESP32-CSI-Tool repository, what ESP-IDF is, and a detailed breakdown of your workflow script so you understand *why* you are running each command.

## 1. What is ESP-IDF?
**ESP-IDF (Espressif IoT Development Framework)** is the official and native software development framework for the ESP32 family of chips. 
While many beginners use the Arduino IDE to program ESP32s, Arduino hides a lot of advanced features. ESP-IDF gives you low-level access to the hardware, the FreeRTOS operating system, and the Wi-Fi drivers. 
**Why we need it here:** To extract Wi-Fi CSI (Channel State Information), we need access to the deep internals of the Wi-Fi driver, which the Arduino core does not easily expose.

## 2. What is this Repository About?
This repository is based on the **ESP32-CSI-Tool** created by Steven M. Hernandez.
* **What is CSI?** Channel State Information describes how Wi-Fi signals propagate from the transmitter to the receiver. It represents how the radio waves scatter, fade, and bounce off objects and people in a room.
* **How it works:** By analyzing these microscopic changes in the Wi-Fi signal reflections, we can detect movements in the room without cameras. This can be used for breathing detection, presence detection, hand gestures, and in your case, **Fall Detection**.

### What are `active_ap` and `active_sta`?
In Wi-Fi network terminology:
* **AP (Access Point):** The router or hotspot that broadcasts the Wi-Fi signal for other devices to connect to.
* **STA (Station):** The client device (like a phone, laptop, or an ESP32) that connects *to* an Access Point.

This repository provides two primary ways to collect CSI data:
1. **`active_sta` (Station Mode):** This is the code you are currently using. The ESP32 acts as a normal Wi-Fi client and connects to a router or your phone's Mobile Hotspot. Every time the router (or your phone) sends a packet (like a ping reply) to the ESP32, the ESP32 calculates the CSI of that incoming packet. 
2. **`active_ap` (Access Point Mode):** In this mode, the ESP32 *becomes* the router. You connect your phone or laptop directly to the Wi-Fi network broadcasted by the ESP32. Whenever your device sends packets to the ESP32, the ESP32 calculates the CSI. 

*Why use one over the other?* `active_sta` is generally preferred when you want your phone to act as the trigger (by pinging) because phones handle hotspot configurations easily, and it's easier to grab logs on a computer attached to the ESP32.

### Deep Dive into `main.cc`
Regardless of whether you use `active_ap` or `active_sta`, the heart of the logic is inside their respective `main.cc` files. 
Here is exactly what happens when the ESP32 boots up and runs `main.cc`:

1. **`app_main()` entry point:** In ESP-IDF C++ programs, execution always starts at `app_main()`.
2. **`config_print()`:** It prints out a huge block of text showcasing your current configuration settings (SSID, Password, Target, Baudrate, etc.) over the serial monitor. This helps verify your `menuconfig` settings actually saved.
3. **Hardware Storage init (`nvs_init`, `sd_init`):** Initializes the Non-Volatile Storage (the ESP32's internal flash drive) which the Wi-Fi driver needs to securely store encryption keys and connection profiles.
4. **Wi-Fi Initiation (`station_init()` or `softap_init()`):** 
   * **In `active_sta`:** Spawns a background task to handle Wi-Fi connection states. It tells the ESP32 to connect to the SSID and Password you defined in `menuconfig`. It registers an event handler (`event_handler`) to listen for the "Got IP address" moment.
   * **In `active_ap`:** Configures the ESP32 to broadcast an SSID network instead of joining one, waiting for devices to join.
5. **The CSI Magic (`csi_init()`):** This function is called from the `_components/csi_component` folder. It registers a low-level callback *directly* with the ESP32's Wi-Fi baseband hardware. It tells the chip: *"Every time you receive a Wi-Fi radio packet, grab the physical layer properties, format them into a string starting with `CSI_DATA`, and print them to the USB Serial port."*
6. **Background Tasks:** Finally, `active_sta` spawns a FreeRTOS background task (`socket_transmitter_sta_loop`) which runs constantly. If you were sending CSI data over UDP (a network socket) instead of a USB cable, this loop would handle actively transmitting the collected data out to the network.

---

## 3. Demystifying Your Workflow Script
Here is the step-by-step breakdown of your master cheat sheet so you understand exactly what each command is doing.

### Phase 1: Install Dependencies
* **Visual Studio Build Tools & Git:** ESP-IDF relies on a toolchain (compilers like GCC, CMake, Ninja) to build the C/C++ code into a binary file that the ESP32 can run. Git is required to clone the ESP-IDF repository and its submodules.

### Phase 2: Download & Fix ESP-IDF v4.4
CSI tools are notoriously sensitive to ESP-IDF versions because Espressif occasionally changes the internal Wi-Fi driver APIs. version `v4.4.4` is known to be stable for this tool.
* **`git clone -b v4.4.4 ...`**: Downloads the specific framework version.
* **Automated Fix 1 (`gdbgui`)**: `gdbgui` is a debugging tool included in older ESP-IDF versions. It is broken on newer Python versions. By commenting it out, you prevent the installation script from crashing.
* **`install.bat`**: Downloads the cross-compilers (tools that run on Windows but build code for the ESP32 processor).
* **`export.bat`**: This is crucial. It adds the ESP-IDF tools to your Windows command prompt environment variables. Without this, your terminal doesn't know what `idf.py` is.
* **Automated Fix 2 (`setuptools`)**: Newer versions of Python's `setuptools` removed features that the old ESP-IDF scripts relied on. Downgrading it prevents breaking issues when compiling.

### Phase 3: Download CSI Tool & Patch C++
* **`git clone ... esp32-csi-tool`**: Downloads the repository.
* **Automated Fix 3 (Patch `main.cc`)**: The ESP32-S3 is a newer chip compared to the classic ESP32. Between different ESP-IDF versions, Espressif reorganized the header files (moving flash memory and MAC address functions out of `spi_flash_mmap.h` and into their own files). This powershell command patches the C++ source code to use the correct include files for the S3 chip so it doesn't fail with "file not found" errors during compilation.

### Phase 4: Configure ESP32-S3 Target
* **`idf.py set-target esp32s3`**: Tells the build system not to compile for the classic ESP32, but specifically for the architecture of the ESP32-S3.
* **`idf.py menuconfig` Changes Explained:**
  * **Baudrate 921600:** CSI generates an enormous amount of data (thousands of numbers per second). If the USB serial baud rate is standard (like 115200), the ESP32 will choke trying to print the data and will crash or drop packets. 921600 is fast enough to handle the data pipe.
  * **Wi-Fi CSI Checkbox:** This flips the switch deep in ESP-IDF to turn on the hidden hardware feature that exposes CSI data.
  * **FreeRTOS Tick Rate 1000:** The ESP32's OS (FreeRTOS) usually updates its clock every 10ms (100Hz). Setting it to 1000Hz (1ms) makes the system more responsive, which is critical when trying to process high-frequency Wi-Fi packets without missing any.

### Phase 5: Flash and Get IP
* **`idf.py flash monitor`**: This is a combination command. `flash` compiles your C++ code into `.bin` files and uploads them over the USB cable to the ESP32-S3. `monitor` opens a serial terminal so you can see the `printf` output from the chip.
* **"Got ip"**: Once connected to your phone's hotspot, the ESP32 gets an IP address. You need this to direct traffic (pings) *to* the ESP32.

### Phase 6: Record the Data
This is where the magic happens.
* **Pinging from your phone:** By continuously pinging the ESP32's IP from your phone, you are forcing Wi-Fi packets to travel through the air, bounce off your body, and hit the ESP32 antenna. 
* **`idf.py monitor | findstr "CSI_DATA" > falling_01.csv`**:
  * `idf.py monitor`: Reads the live serial output from the ESP32.
  * `|` (Pipe): Takes that output and passes it to the next command.
  * `findstr "CSI_DATA"`: Filters out all the boot logs and system noise, keeping ONLY the lines starting with `CSI_DATA`.
  * `> falling_01.csv`: Directs those filtered CSI lines into a CSV file.
* **Perform the fall:** As you fall, you disrupt the physical path of the Wi-Fi ping traveling from your phone to the ESP32. The ESP32 captures this disruption in the CSI data, which is successfully printed to serial and saved to your CSV file for later training your Fall Detection ML model.
