# Huawei nova 2 (PIC-TL00) Root — 进度存档

> 存档时间：2026-10-25  
> 状态：**软件 testpoint 已成功，手机当前处于 VCOM/BOOTROM（黑屏），尚未解锁 Bootloader、尚未 root。**  
> 下次继续先读本文件，尤其是「不要做」和「明天二选一」。

## 1. 设备信息

| 项 | 值 |
|---|---|
| 型号 | 华为 nova 2（PIC-TL00，移动4G+） |
| 系统 | EMUI 8.0.0 / Android 8.0.0 |
| 版本 | 8.0.0.377(C01)，安全补丁 2020-05-01 |
| Bootloader 报告 | 8.0.0.386(C01)，USER/FB 均 LOCKED |
| SoC | Kirin 659 / hi6250 |
| 内核 | 4.4.23+（构建 2022-11） |
| SN | <DEVICE_SN> |
| 当前 USB | `USB SER`，`USB\VID_12D1&PID_3609`，WinUSB (libwdi, oem80.inf)，**无 COM 口** |
| 键盘 | `VID_09DA&PID_2268 MI_00` = HidUsb / HID Keyboard Device（已恢复） |

VCOM 当前可被 pyusb/libusb 看到：`12d1:3609`（bus/addr 会随重枚举变化）。  
**手机屏幕黑屏是 VCOM/BOOTROM 的正常现象，不是关机。**

## 2. 已完成的关键步骤

### 2.1 固件与镜像

- 从 Huawei Firmware Finder 数据库找到 PIC-TL00 8.0.0.377(C01) 的完整 OTA 目录并下载：
  - `tools/firmware/update-377.zip`，1,915,377,768 字节，MD5 `5EC1884EB11E4958A1ECA4131E0D5E74`（与官方 filelist 一致）。
- 解出 `UPDATE.APP`（3,992,312,976 字节）：`tools/firmware/377/UPDATE.APP`。
- 已提取原厂分区到 `tools/firmware/377/parts/`（含 XLOADER / KERNEL / RAMDISK / RECOVERY_RAMDISK / VBMETA / RECOVERY_VBMETA）。

### 2.2 软件 testpoint（免拆机）已成功

官方 **Kirin-Tool v2.4.2** 的软件 testpoint 对 `ONLINE_UPDATE` 包会失败：

> `Failed to Software Testpoint the device! Make sure you are using the Base UPDATE from the exact or newer firmware...`

原因：我们只有 OTA 的在线包（`dload/PACKAGE_TYPE.img` = `ONLINE_UPDATE`），官方工具没有把它转成离线包/处理鉴权。

改用开源流程（kasnria001/huawei-usbdload-tool 的协议）：把包离线化后通过 **DBAdapter COM（COM8）** 发送，**成功进入 VCOM**：

- `dload/PACKAGE_TYPE.img` → `OFFLINE_UPDATE` + CRC 碰撞（`pk_cracked.bin`，31 字节）
- `dload/XLOADER.img` → 前 0x8000 与官方 `fastboot/payload`（=`crc_hacked.bin`，SHA256 一致）做 XOR，CRC 保持一致
- `dload/XLOADER.img.header` → **保持名字 `XLOADER`**（改成 `PRELOADER` 反而被设备拒绝）
- `dload/unlockcode` = `HW7x27\xff\xff`（8 字节）
- `dload/list.txt` 到 XLOADER 停止
- 发送脚本：`analysis/usbd-usbdload.py`；发送成功，手机进入 `12d1:3609` VCOM

**注意：**`tools/kirin-tool/dload/` 现在是**已离线化/已打补丁**的状态；原始文件备份在 `analysis/dload-backup/`（`XLOADER.img`、`XLOADER.img.header`、`PACKAGE_TYPE.img`、`list.txt`）。

如果需要重新发送（手机退出 VCOM 时）：

```powershell
cd "D:\Reverse testing\huawei-nova2-root\tools\kirin-tool"
"1" | & "D:\Reverse testing\huawei-nova2-root\.venv\Scripts\python.exe" "D:\Reverse testing\huawei-nova2-root\analysis\usbd-usbdload.py"
```

### 2.3 卡在 VCOM 驱动（当前阻塞点）

- PotatoNV 的 `Potato.ImageFlasher.ImageFlasher.Open(String portName)` **需要 COM 串口**，不是 WinUSB/libusb。因此 PotatoNV 的 `Target device` 为空是必然的。
- Zadig 的 WinUSB/libusbK 对 PotatoNV **无效**；而且一次误把键盘（VID_09DA…MI_00）绑成 libusbK，导致键盘失效。
  - 已执行 `pnputil /delete-driver oem85.inf /uninstall /force`，键盘恢复为 HidUsb/kbdhid。**不要再给键盘装 Zadig 驱动。**
- HiSuite 14.0.0.380 已用 winget 安装（`C:\Program Files (x86)\HiSuite`），但它带来的驱动没有 PID 3609 模型（`HUAWEI06` 对应的是 PID 3650），`Have Disk` 被硬件 ID 过滤，装不上。
- 旧版 `hw_usbvcom.inf`（唯一匹配 3609 的 INF）与它的 `.sys/.cat` **版本哈希不匹配**：
  > `无法添加驱动程序包: 文件的哈希值不在指定的目录文件中。`
- Secure Boot = **True**，`bcdedit /set testsigning on` 被安全引导策略拒绝，测试签名这条路被挡住。
- pyusb + libusb 已确认能看到 `12d1:3609`，说明 USB 设备本身没问题，缺的就是一个能暴露 COM 的 VCOM 驱动。

## 3. 现在不要做

- **不要拔 USB、不要长按电源、不要关机。** 手机在 VCOM；patched XLOADER 已写入，正常系统起不来，黑屏是正常的。
- 不要再跑官方 Kirin-Tool 的 `Enter`（它会重建 dload，且不支持在线包）。
- 不要再给键盘/手机乱装 Zadig 驱动；键盘已恢复。
- 不要删除 `tools/kirin-tool/dload/`、`analysis/dload-backup/`、`tools/firmware/377/parts/`。
- 解锁会**清空手机数据**；手机当前不可作为正常机使用。

## 4. 明天从这里继续（二选一）

### 方案 A：进 BIOS 关 Secure Boot + 测试签名（推荐，最稳）

1. 重启进 BIOS（常见 F2 / Del / F10，依机型），找到 **Security → Secure Boot → Disabled**，保存退出。
2. 回到 Windows，管理员 PowerShell：
   ```powershell
   Confirm-SecureBootUEFI      # 应为 False
   bcdedit /set testsigning on
   ```
   重启（桌面会出现“测试模式”水印）。
3. 设备管理器 → `USB SER` → 更新驱动程序 → 浏览我的电脑 → 让我从列表选取 → **从磁盘安装**：
   ```
   D:\Reverse testing\huawei-nova2-root\tools\vcom-test\hw_usbvcom.inf
   ```
   （这份 INF 已去掉 `CatalogFile`，且含 `USB\VID_12d1&PID_3609` 模型）
   选 **`HUAWEI USB COM 1.0`** → 安装；测试模式下允许未签名，出现“无法验证发布者”选“仍然安装”。
4. 端口出现 **`HUAWEI USB COM 1.0 (COMx)`** 后，二选一：
   - **Kirin-Tool**：CPU 选 `Kirin 65x_a` → `VCOM Operations` → `Unlock`（Unlock Fastboot，会提示 ARB 永久增加）→ `Security Tools` → `Unlock Bootloader`（写解锁码、清数据）。
   - **PotatoNV**：现在有 COM，`Target device` 会出现 → `Bootloader = Kirin 65x (A)` → `Start!`，保存 16 位解锁码 → 重启到 fastboot 执行 `fastboot oem unlock <code>`。
5. 验证：
   ```powershell
   fastboot oem get-bootinfo   # 应为 UNLOCKED
   ```
6. 完成后可恢复安全设置：`bcdedit /set testsigning off` → 重启；需要的话再进 BIOS 重新打开 Secure Boot。

### 方案 B：不改 BIOS，用 pyusb 直接写 VCOM（耗时）

- 思路：按 PotatoNV 源码 `Potato.ImageFlasher/ImageFlasher.cs` 的串口协议，改为 **pyusb bulk**：
  - VCOM `12d1:3609`，interface 0，bulk **OUT 0x01 / IN 0x81**（Linux 文档确认）。
  - 上传 `tools\PotatoNV-next-v2.2.1-2022.03-x86\bootloaders\hisi65x_a\` 里的 `xloader.img` / `fastboot.img` 到源码中的地址。
  - 进入 fastboot 后写 NVME 解锁属性（`getvar:nve:...`，见 Kirin-Tool/PotatoNV 的 `WriteKEY`），或直接 `fastboot oem unlock`。
- 适合不想动 Secure Boot 的情况；实现/调试工作量较大，pyusb 已能枚举设备。

### 方案 C（不推荐，优先级低）

- 找一个真正匹配 `USB\VID_12D1&PID_3609` 的 WHQL VCOM 驱动包（HiSuite 14 没有；旧 `hw_usbvcom` 包与 catalog 不匹配）。能找到的话可直接走 Kirin-Tool。

## 5. 解锁后的 root（已备好）

- 原厂 RAMDISK：`tools/firmware/377/parts/RAMDISK.img`
  - `ANDROID!`，kernel_size=0，ramdisk_size=8,539,331，page=2048
- Magisk：`tools/Magisk-v25.2.apk`（SHA256 `0BDC32918B6EA502DCA769B1C7089200DA51EA1DEF170824C2812925B426D509`）
  - 用 Magisk App 在手机上 patch `RAMDISK.img`，**保留 AVB/dm-verity 与强制加密**；
  - `fastboot flash ramdisk magisk_patched.img`；
  - 启动后 `adb shell su -c id` 验证。
- 回退/兜底：
  - 官方 TWRP：`tools/twrp/twrp-3.4.0-0-prague.img`（SHA256 `0620F8454CFF7F0EA3CD61450FC8021AD50D81E6D413C5AC1D028ADD5DE9FA0C`）
  - 原厂 `RECOVERY_RAMDISK.img` / `KERNEL.img` / `XLOADER.img` 在 `tools/firmware/377/parts/`。
- 硬件兜底：PotatoNV + 拆机短接；测试点图 `analysis/nova2-testpoint.png`（红色标记在主板右下、金色焊盘上方）。

## 6. 文件与哈希

### 固件/分区

| 文件 | 大小 | SHA256 |
|---|---:|---|
| `tools/firmware/377/parts/XLOADER.img`（原厂） | 69,568 | `5A796B3A09F38164705590F1C685BEE2EADA56154C872C1D625382FBF98F8643` |
| `tools/firmware/377/parts/KERNEL.img` | 25,165,824 | `9864D05E5E42BC2A3CDAB55B557F3966D0FEFBE09B0E860E11928791331DA5BD` |
| `tools/firmware/377/parts/RAMDISK.img` | 16,777,216 | `C70BA8CEE323AA54318CF053253C96CC8C7CD96C40AE9CD6E71E99B36E5DE261` |
| `tools/firmware/377/parts/RECOVERY_RAMDISK.img` | 33,554,432 | `ACE76FCD350D3C86EF3FAE556D68AF9C7A60184134AD1DB88ECAE9F5292E517D` |
| `tools/firmware/377/parts/VBMETA.img` | 10,176 | `1ED2BDED94399ACEFD537B1154DAC142B2C64D26BB030E5227F38A84AB7BD411` |
| `tools/firmware/377/parts/RECOVERY_VBMETA.img` | 7,104 | `452F597C13EF123950FBABE5EE53405082C983F47F1D39AAF62D9D92F0F40D55` |
| `tools/kirin-tool/dload/XLOADER.img`（已 CRC 碰撞） | 69,568 | `3DAD8BDC04239CC23F0141DE80E86452D73D56F61E3EAA44E363D25E63A579E2` |
| `tools/vcom-test/hw_usbvcom.inf`（去掉 CatalogFile） | 2,538 | `5C2860E5413B4CB680C2DE544BEDA6BBF98585B96DD080A7DE4E68FAA02DEC02` |

### 其他关键文件

- `tools/kirin-tool/`：官方 Kirin-Tool v2.4.2（zip SHA256 `DFB8E7FCE2F6FEF26FFCCAA9BC3B2B76A3C32F654B16FF784C906857AC298537`）
- `tools/kirin-tool/dload/`：已离线化包（`PACKAGE_TYPE.img` 31B、`unlockcode` 8B、`list.txt` 75B）
- `analysis/dload-backup/`：原始 XLOADER/header/PACKAGE_TYPE/list 备份
- `tools/huawei-dbadapter/`：WHQL 驱动包（`hw_cdcacm` / `hw_quser` / `hw_usbdev` 等，`.cat` 有效）
- `tools/huawei-usb-driver/X64/`：旧华为驱动（含 3609 的 `hw_usbvcom.inf/.sys/.cat`，cat 哈希不匹配）
- `tools/PotatoNV-next-v2.2.1-2022.03-x86/`：PotatoNV（需要 COM；`hisi65x_a` 引导已含）
- `tools/zadig-2.9.exe`：Zadig（本次未解决问题；不要再误装键盘）
- `tools/Magisk-v25.2.apk`、`tools/twrp/twrp-3.4.0-0-prague.img`
- `.venv/`：Python 3.14，已装 `pyserial`、`crccheck`、`pyusb`、`libusb-package`
- `analysis/`：脚本、截图、`usbd-usbdload.py`、`pyusb_scan3.py`、`vcom_check.py` 等

## 7. 关键来源

- Firmware Finder 数据：`https://github.com/felpcereti/Huawei-Firmware-Finder`（`raw-data/*.json`）
- 377(C01) OTA 目录：`http://update.dbankcdn.com/download/data/pub_13/HWHOTA_hotaMigrate_900_9/bd/v3/ca84a76c58bd4243a9797f3fae2ac574/`
- 开源 USB DLOAD：`https://github.com/kasnria001/huawei-usbdload-tool`
- PotatoNV：`https://github.com/mashed-potatoes/PotatoNV`
- Kirin-Tool：`https://kirintool.cfd/` / `https://github.com/kethily-daniel/Kirin-Tool`
- 华为 USB COM 驱动资料：`https://treexy.com/products/driver-fusion/database/ports-com-lpt-serial/huawei/dbadapter-reserved-interface/`
- Linux USB Update 检测/接口映射：`https://github.com/Redminote11tech/kirin-tool-linux/blob/main/docs/usb-update-linux-detection.md`

## 8. 风险与回滚

- 软件 testpoint 有**小概率变砖**；成功进入 VCOM 后，硬件兜底是拆机短接 + PotatoNV。
- 解锁 Bootloader 会**清空数据**；当前手机在 bootrom，数据不可访问，解锁前无法备份。
- 方案 A 会关闭 Secure Boot / 开启测试签名，属于降低系统安全保护；完成后可恢复。
- 任何时候不要拔线/断电；如果手机重启后退出 VCOM，先尝试重新进入 5%（音量上+音量下+电源）并重跑 `usbd-usbdload.py`；若不行再考虑硬件 testpoint。

---

## 9. 2026-10-25 实机进展（已解锁，系统恢复中）

- **Bootloader 已解锁**：`USER LockState: UNLOCKED`；解锁码 `<UNLOCK_CODE>`，WVLOCK/USRKEY 已写入 NVME。
- 软件 testpoint、VCOM、PotatoNV 临时 fastboot 均成功；normal bootloader 的 FB LOCKED 会拒绝 `boot`/`oem reboot-recovery`/`erase misc`/`erase metadata`/`flash vendor` 等，FB UNLOCKED 临时 bootloader 可以。
- 已刷回原厂 377 的 `system/vendor/odm/product/kernel/ramdisk/vbmeta/cache/XLOADER/recovery_ramdisk`；`bootfail_info`（曾为 15 次失败）和 `misc` 已清零；userdata 头尾各 64 MB 已清零。
- 当前仍自动进 eRecovery，系统起不来；正在用 **5% dload 整包重刷 377**（含 FASTBOOT/XLOADER/TEEOS/DTS/ERECOVERY），脚本：
  ```powershell
  Set-Location "D:\Reverse testing\huawei-nova2-root\tools\firmware\377"
  "1" | & "D:\Reverse testing\huawei-nova2-root\.venv\Scripts\python.exe" "D:\Reverse testing\huawei-nova2-root\analysis\usbd-usbdload.py"
  ```
  `dload` 包在 `tools/firmware/377/dload`；`PACKAGE_TYPE.img` 已换成 `tools/usbdload/pk_cracked.bin`（OFFLINE_UPDATE + CRC 碰撞）；XLOADER 保持原厂（不要再打 CRC 碰撞，否则会回 VCOM）。
- 注意：`tools/twrp/twrp-3.4.0-0-prague.img` 是 **P8 Lite 2017（prague）** 的 TWRP，不是 nova 2（PIC/Picasso）专用；仅临时用于 ADB 诊断/清零，不要长期保留。
- 下一步：5% 全量写完后重启；若仍 eRecovery，重点查 `oeminfo`/`frp`/`patch` 和 386 XLOADER/ARB，必要时找 PIC-TL00 8.0.0.386 完整固件。

## 10. 2026-10-25 最终结果（系统已启动，未 root）

- **系统已成功启动**：原厂 377；5% 全量 dload 已写回 system/vendor/odm/product/kernel/ramdisk/vbmeta/cache/XLOADER/recovery_ramdisk/FASTBOOT/TEEOS/DTS/ERECOVERY。
- **根因**：`/cust` 分区（mmcblk0p53，192 MB）没有文件系统（ext4 superblock 全零），导致系统和 factory reset 一直失败；在 TWRP 里执行 `mke2fs -t ext4 -F -L cust /dev/block/bootdevice/by-name/cust` 后系统成功启动。
- **Bootloader**：`USER LockState: UNLOCKED`，`FB LockState: LOCKED`；解锁码 `<UNLOCK_CODE>`（建议保存）。开机出现 unlocked 警告是正常的。
- **未 root**：用户决定只刷系统，不 root；第 5 节的 Magisk 步骤保留，随时可做。
- **注意**：`/cust` 目前是空 ext4（运营商定制内容缺失）；data 已清空；解锁状态下部分银行/支付 App 可能拒绝，OTA 可能受影响；不要随意 `fastboot oem lock` 重新上锁。
- **验证**：系统可正常启动；`adb shell getprop ro.boot.flash.locked` 应为 `0`。

**下次开工第一句：** 读本文件 → 手机已能进系统；root 未做；如要 root 按第 5 节 Magisk 流程。
