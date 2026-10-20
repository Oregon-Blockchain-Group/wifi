# Hardware Research & Prototyping Plan

**Projects:** Wi-Fi Environmental Sensing · AI Smart Helmet
**Status:** Research complete. Preparing initial prototypes.
**Last updated:** October 20, 2026

> **TL;DR:** Build two cheap, working prototypes on one MacBook before buying advanced hardware.
> - **Wi-Fi sensing:** router + 2 ESP32 boards + MacBook. Detect movement from Wi-Fi signals.
> - **Smart helmet:** USB webcam + MacBook. Detect objects with local AI and show them on a screen.
>
> **Next action:** Confirm component compatibility, confirm the budget, buy the core hardware, and start Phase 1.

---

## 1. The Two Projects

| | Wi-Fi Environmental Sensing | AI Smart Helmet |
| --- | --- | --- |
| **Idea** | Use Wi-Fi signals to detect movement and changes in a room. | Use computer vision to recognize objects and show info about the surroundings. |
| **First goal** | Collect wireless measurements, detect movement, and show the results on a laptop. | Run an object-detection model locally and show the detected objects on a screen. |
| **Long-term goal** | AI-assisted object localization and spatial reconstruction from wireless signals. | A compact bicycle helmet with onboard AI, environmental sensing, and a near-eye heads-up display (HUD). |

The projects are independent. Both focus on AI, environmental sensing, and real-time visualization.

**How we'll work:**
1. Buy the minimum hardware for both prototypes.
2. Get sensor data collection working.
3. Run AI models locally.
4. Build basic real-time visualizations.
5. Validate performance with controlled experiments.
6. Add hardware only when a new capability actually needs it.

---

## 2. What to Buy

This list assumes we're starting from scratch. If a team member already owns a compatible part, cross it off.
Prices are **rough planning allowances, not verified retail prices.**

### 2.1 Shopping list

| Item | Qty | Used for | Project | Priority | Est. cost |
| --- | --- | --- | --- | --- | --- |
| Apple Silicon MacBook Pro | 1 | AI inference, development, data processing, visualization | Both | Required | $1,500–$3,000 |
| Wi-Fi router (2.4 GHz) | 1 | Generates the Wi-Fi signals we measure | Wi-Fi | Required | $40–$100 |
| ESP32-WROOM-32 dev board (verified CSI support) | 2 | Transmit and receive Wi-Fi; collect CSI data | Wi-Fi | Required | $12–$30 (pair) |
| USB data cable (micro-USB to USB-C; must carry data, not just power) | 2 | Program the boards and transfer data | Wi-Fi | Required | $10–$20 |
| USB webcam (1080p preferred) | 1 | Video for object detection | Helmet | Required | $20–$60 |
| Camera tripod or stand | 1 | Position the camera | Helmet | Required | $10–$25 |
| USB-C hub with USB data ports | 1 | Connect several devices to the MacBook | Both | Recommended | $15–$40 |
| USB power adapter | 2 | Power the ESP32 boards on their own | Wi-Fi | Recommended | $10–$20 |
| ESP32 stand or mount | 2 | Keep sensor positions fixed | Wi-Fi | Recommended | $10–$30 |
| Measuring tape | 1 | Record sensor placement and distances | Wi-Fi | Recommended | $5–$15 |
| External SSD, 1 TB | 1 | Datasets, models, recordings, results | Both | Recommended | $60–$120 |
| Power strip | 1 | Power multiple devices | Both | Recommended | $10–$20 |
| Small external monitor or HDMI display | 1 | Simulate the future HUD | Helmet | Optional | $50–$120 |
| HDMI cable or USB-C display adapter | 1 | Connect the display | Helmet | Optional | $10–$25 |
| Camera USB cable | 1 | Only if the webcam doesn't include one | Helmet | If needed | — |

**Don't buy yet:** Raspberry Pi, dedicated AI accelerator, mmWave radar, depth camera, software-defined radio, helmet-mounted display optics, wearable battery system, custom PCB.

### 2.2 Budget

| Category | Est. cost |
| --- | --- |
| Shared hardware (MacBook, router, hub, SSD, power strip) | $1,625–$3,280 |
| Wi-Fi sensing (ESP32s, cables, adapters, stands, tape) | $47–$115 |
| Computer vision (webcam, stand, display, display cable) | $90–$230 |
| **Total** | **$1,762–$3,625** |

- The total assumes we have to buy the MacBook and router.
- If we already have them, the extra cost is about **$137–$345**, not counting shared accessories and storage.
- The external display is optional for the first computer vision demo.

### 2.3 What to look for

- **MacBook Pro:** Apple Silicon with at least 16 GB unified memory (24–32 GB+ for larger local models) and at least 512 GB storage. Less memory still works with smaller models.
- **Wi-Fi router:** 2.4 GHz support, configurable wireless settings, stable operation, and ESP32 devices can connect to it. A basic consumer router is enough. Wi-Fi 6 or 7 isn't needed.
- **ESP32 boards:** Use an ESP32-WROOM-32-based board with a USB programming interface and documented compatibility with Espressif's CSI examples. **Verify the exact board model before buying.**
  - Espressif's own **ESP32-DevKitC-32E** (PCB antenna) or **ESP32-DevKitC-32UE** (IPEX connector for an external antenna) both use this module. The DevKitC has a micro-USB port.
  - ESP-CSI notes that an external IPEX antenna gives better results than a PCB antenna, which is directional. That makes the 32UE plus an antenna worth considering.
  - **Alternatives:** ESP-CSI says all ESP32 series chips support CSI: ESP32, ESP32-S2, ESP32-C3, ESP32-S3, ESP32-C5, ESP32-C6, and ESP32-C61. Stick with the original ESP32 at first, since that's what this plan is built around.

### 2.4 Where to buy

Example sources, checked October 20, 2026. Prices change, so confirm them before ordering. Links marked *search* go to a search page; I couldn't load Amazon from a script, so check those links by hand.

| Item | Where |
| --- | --- |
| MacBook Pro | [Apple Store](https://www.apple.com/shop/buy-mac/macbook-pro) · [Apple Certified Refurbished](https://www.apple.com/shop/refurbished/mac/macbook-pro) (cheaper) |
| Wi-Fi router | Example: [TP-Link Archer A7](https://www.tp-link.com/us/home-networking/wifi-router/archer-a7/) (any basic 2.4 GHz router works) |
| ESP32 dev boards | [Mouser: DevKitC-32E](https://www.mouser.com/c/?q=ESP32-DEVKITC-32E) · [Mouser: DevKitC-32UE](https://www.mouser.com/c/?q=ESP32-DEVKITC-32UE) · DigiKey lists the 32UE at about $10 each · [Espressif board info](https://www.espressif.com/en/products/devkits/esp32-devkitc) |
| USB webcam | Example: [Logitech C920s](https://www.logitech.com/en-us/products/webcams/c920s-pro-hd-webcam.960-001257.html) |
| External SSD, 1 TB | Example: [Samsung T7 1 TB](https://www.samsung.com/us/computing/memory-storage/portable-solid-state-drives/portable-ssd-t7-usb-3-2-1tb--blue--mu-pc1t0h-am/) |
| Micro-USB to USB-C data cables | [Amazon *search*](https://www.amazon.com/s?k=micro+usb+to+usb+c+data+cable) |
| USB-C hub | [Amazon *search*](https://www.amazon.com/s?k=usb+c+hub+usb+a+data) |
| USB power adapters | [Amazon *search*](https://www.amazon.com/s?k=usb+wall+charger+5v) |
| ESP32 stands or mounts | [Amazon *search*](https://www.amazon.com/s?k=mini+tripod+phone+mount) |
| Camera tripod or stand | [Amazon *search*](https://www.amazon.com/s?k=webcam+tripod+stand) |
| Measuring tape | [Amazon *search*](https://www.amazon.com/s?k=measuring+tape+25+ft) |
| Power strip | [Amazon *search*](https://www.amazon.com/s?k=power+strip+surge+protector) |
| Small external monitor | [Amazon *search*](https://www.amazon.com/s?k=portable+monitor+usb+c) |
| HDMI cable or USB-C display adapter | [Amazon *search*](https://www.amazon.com/s?k=usb+c+to+hdmi+adapter) |

---

## 3. Prototype Setups

### 3.1 Wi-Fi sensing

```
              Wi-Fi Router
                   │  Wi-Fi signals
          ┌────────┴────────┐
      ESP32 #1          ESP32 #2
    (transmitter)       (receiver)
                            │ USB
                       MacBook Pro
     CSI processing → AI classification → live visualization
```

| ✅ Expect at first | ❌ Don't expect yet |
| --- | --- |
| Collect CSI measurements | Accurate object identification |
| Visualize signal amplitude changes | Precise object coordinates |
| Detect changes caused by movement | Detailed 3D room reconstruction |
| Store experiment data | |
| Train a basic movement classifier | |

### 3.2 Smart helmet (desk prototype)

The first version runs on a desk. Nothing gets mounted on a helmet yet.

```
USB camera → video stream → MacBook Pro
  → AI object detection → object tracking → visualization → external display
```

**Expected:** live camera capture, local AI inference, object recognition, bounding boxes, object tracking, confidence scores, and a basic HUD simulation.

**Note:** A regular camera doesn't measure object distance accurately. Estimating distance needs extra methods or hardware.

---

## 4. Software

Everything runs locally on the MacBook. All of it is free (macOS comes with the Mac; Docker is free under its applicable terms).

| Software | Purpose | Used in |
| --- | --- | --- |
| macOS | Operating system | Both |
| Python | AI and signal-processing development | Both |
| Visual Studio Code | Code editor | Both |
| Git | Version control | Both |
| Docker | Reproducible development environments | Both |
| JupyterLab | Data analysis and experiments | Both |
| NumPy | Numerical processing | Both |
| PyTorch | Advanced AI models and model inference | Both |
| ESP-IDF | ESP32 development | Wi-Fi |
| ESP-CSI | CSI collection examples | Wi-Fi |
| SciPy | Signal filtering | Wi-Fi |
| Matplotlib | Signal visualization | Wi-Fi |
| pandas | Dataset organization | Wi-Fi |
| scikit-learn | Basic machine learning | Wi-Fi |
| OpenCV | Camera input and image processing | Helmet |
| YOLO-compatible model | Object detection | Helmet |
| MLX | AI experiments on Apple Silicon | Helmet |
| Three.js | 3D visualization (future) | Helmet |

**Reference repositories**
- **Wi-Fi sensing:** [ESP-CSI](https://github.com/espressif/esp-csi) · [ESP-IDF](https://github.com/espressif/esp-idf) · [Nexmon CSI](https://github.com/seemoo-lab/nexmon_csi)
- **Computer vision:** [OpenCV](https://github.com/opencv/opencv) · [Ultralytics](https://github.com/ultralytics/ultralytics) · [PyTorch](https://github.com/pytorch/pytorch) · [Apple MLX](https://github.com/ml-explore/mlx)

---

## 5. Roadmap

| Phase | Goal | Tasks | Done when |
| --- | --- | --- | --- |
| **1. Hardware setup** | Get both development setups working | Get the MacBook, router, 2 ESP32 boards, cables and adapters, webcam, and camera stand. Set up Python, install ESP-IDF, and verify all the connections. | Both hardware setups are working. |
| **2. Wi-Fi sensing prototype** | Collect and visualize CSI | Configure the router, flash the ESP32 firmware, set up wireless communication, collect CSI, stream it to the MacBook, store it with timestamps, build a live signal view, and test movement detection. | A demo responds to movement in the room. |
| **3. Computer vision prototype** | Detect objects with local AI | Connect the camera, set up OpenCV, download a pretrained detection model, run it locally, show the detections, add tracking, measure inference latency, and build a basic HUD-style interface. | Real-time object detection works. |
| **4. Data collection & AI** | Repeatable experiments and measured performance | Define experiment procedures, collect empty-room and movement CSI, label the datasets, train a basic CSI classifier, evaluate detection accuracy, record computer vision performance, and compare results across sessions. | We have the first datasets, trained models, and performance numbers. |
| **5. Visualization** | Better presentation of sensor output | Build one dashboard that shows live Wi-Fi data and computer vision predictions, stores experiment history, and adds confidence scores. Explore basic 2D spatial views and evaluate what 3D visualization would need. | A local dashboard monitors both prototypes. |

### 5.1 Success criteria

These are proposed starting targets. Adjust them once we see real data.

| Phase | Passes when |
| --- | --- |
| 1. Hardware setup | Both ESP32 boards flash an ESP-IDF example and print to the MacBook's serial console. The webcam shows a live feed in OpenCV. |
| 2. Wi-Fi sensing | CSI streams to the MacBook for 10 minutes without stalling. A person walking through the room makes a visible change in the live signal view, compared with an empty room. |
| 3. Computer vision | A pretrained detector runs locally at **15 FPS or more**, with **100 ms or less** from camera frame to on-screen box. |
| 4. Data & AI | At least 3 recorded sessions. The CSI classifier tells "empty" from "movement" with **90% or better accuracy** on a session it wasn't trained on. |
| 5. Visualization | The dashboard shows live Wi-Fi data and camera detections together, with **less than 1 second** of lag. |

---

## 6. Future Hardware (not needed for the first prototypes)

**Wi-Fi sensing**

| Component | Purpose |
| --- | --- |
| More ESP32 boards | Multi-node sensing |
| MIMO Wi-Fi hardware | More advanced spatial measurements |
| Software-defined radio | RF experiments |
| mmWave radar | Range and motion measurements |
| Depth camera | Geometric room mapping |
| Raspberry Pi | Standalone processing |

**Smart helmet**

| Component | Purpose |
| --- | --- |
| Embedded AI processor | On-device inference |
| Compact camera module | Wearable video capture |
| IMU | Orientation and motion tracking |
| Depth sensor | Distance estimation |
| Micro-OLED display | Visual output |
| Optical combiner or waveguide | Near-eye HUD |
| Battery | Portable power |
| Power-management board | Safe power delivery |
| Custom enclosure | Protects the components |
| Mounting hardware | Secure attachment |

**Future helmet pipeline:**
```
Compact camera → edge AI chip → object detection → object tracking
  → HUD rendering → microdisplay → optical lens → rider
```
The final design also needs motion sensing, power management, thermal design, and proper mounting.

> ⚠️ **Safety:** Wearable prototypes must not weaken the helmet's protection or block the rider's view. Do the first tests on a stationary rig.

---

## 7. Known Limitations

- **Wi-Fi sensing:** Basic ESP32 CSI can't reliably identify arbitrary objects. Movement detection is sensitive to the environment, and multiple people or objects make the signal ambiguous. CSI doesn't directly give a 3D point cloud, so accurate spatial reconstruction needs more advanced sensing and algorithms.
- **Computer vision:** Detection only works on what the camera can see. Poor lighting and blocked views hurt performance. Standard cameras don't measure real-world depth. Accuracy varies by object type and environment, and real-time speed depends on the hardware and model size.
- **Wearable hardware:** Keep power use low. Heat and weight matter. The display must not block the rider's view. Embedded AI will be slower than the MacBook. Helmet safety and regulatory requirements must be evaluated before any practical use.

---

## 8. Privacy, Legal & Safety Rules

These apply from day one.

- **Wi-Fi sensing:** Only run experiments in spaces where we have permission. Get consent from participants. Don't monitor neighboring private areas. Don't capture the contents of unrelated communications. Keep radio hardware within applicable FCC requirements.
- **Computer vision:** Get consent before recording identifiable people. Process locally when possible. Don't store video we don't need, and protect the recordings we keep. Provide clear controls to turn recording off.
- **Smart helmet:** Don't modify the helmet's protective structure. Don't block the rider's field of view. Use proper battery protection. Evaluate heat, weight, and mounting safety. Never rely on experimental detection for collision avoidance.

---

## 9. Bottom Line

- **Wi-Fi sensing:** Start with a router, 2 ESP32 boards, and the MacBook. Focus on collecting CSI, detecting movement, and visualizing it live.
- **Smart helmet:** Start with a USB camera, the MacBook, and a local computer vision model. Focus on detection, tracking, and HUD simulation.
- **Shared approach:** The MacBook is the main workstation for both projects. Each project keeps its own sensing pipeline, and both share tools for data processing, model development, storage, and visualization.

**The first milestone isn't a finished 3D room scanner or a wearable helmet.** It's proving that we can reliably collect real sensor data, process it locally, and show meaningful results. Once that works, we can make informed decisions about more sensors, embedded computing, and wearable integration.

**Status:** Hardware procurement and initial development planning.
