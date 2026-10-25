# 华为 nova 2（PIC-TL00 / Kirin 659）免拆机软件 testpoint 解锁 Bootloader 教程

> 测试设备：Huawei nova 2 **PIC-TL00**，EMUI **8.0.0.377(C01)**，Android 8.0.0，Kirin 659 / hi6250，内核 4.4.23+，bootloader 构建 **8.0.0.386(C01)**。  
> 结果：`USER LockState: UNLOCKED`，系统恢复为原厂 377 并可正常启动；**未做 root**。  
> 本文是实机记录，不是通用工具。不同型号、SoC、EMUI 版本的分区、地址和校验都可能不同。

---

## 0. 风险与适用范围

**请先读完再动手。**

- 解锁会**清空用户数据**；bootrom/VCOM 状态下无法备份。
- 软件 testpoint 有**变砖风险**；本文的操作包含写入 XLOADER/FASTBOOT/NVME 等关键分区。
- 只对**你自己的设备**操作；不要用于他人的设备或商业解锁。
- 不要把这个流程套到其他华为机型；Kirin 65x 的 bootloader 镜像/地址不通用。
- 需要拆机短接作为兜底；如果不敢承担风险，请不要开始。
- 固件、bootloader、驱动、Magisk/TWRP 等第三方材料有各自的许可证；**不要把它们打包进公开仓库**。
- 本文不使用、也不分发任何设备的 SN、IMEI 或解锁码；示例统一用占位符。

**时间/精力：** 顺利的话 1–2 小时；遇到 eRecovery 循环可能是一整天。本文第 8 节就是为这种情况写的。

---

## 1. 原理概览

EMUI 8 的 5% USB Update 模式会按 `UPDATE.APP` 里的镜像头写分区。它对每个镜像做**分块 CRC 校验**（0x8000 一块，CRC16-X25），但在我们测试的版本上**没有对 XLOADER 做整体签名校验**。利用这一点：

```text
原厂 EMUI
  -> 进入 5% USB Update
  -> 发送“离线化 + CRC 碰撞”的 dload 包
  -> 写入一个故意损坏的 XLOADER
  -> 重启后 XLOADER 崩溃，bootrom 落入 VCOM (12D1:3609)
  -> pyusb 上传 PotatoNV 临时 USB bootloader
  -> 临时 fastboot (18D1:D00D, FB UNLOCKED)
  -> 写 NVME: WVLOCK=解锁码, USRKEY=SHA256(解锁码)
  -> 恢复原厂 XLOADER
  -> 正常 bootloader 执行 fastboot oem unlock <code>
  -> USER LockState: UNLOCKED
```

解锁后如果遇到 eRecovery 循环，见第 8 节；我们这次的决定性修复是**格式化 `/cust` 分区**。

> 这不是签名绕过。CRC 碰撞只骗过 update-binary 的分块 CRC，让它接受一个会崩溃的 XLOADER；系统镜像仍然是官方签名的。

---

## 2. 工具链

### 2.1 主机

- Windows 10/11，PowerShell 7，管理员权限（安装驱动/操作 USB）
- Python **3.14**（建议每项目独立 `.venv`）
- Android platform-tools（`adb`、`fastboot`），建议用最新版
- 质量好的 USB 数据线；不要用劣质 hub；全程接充电器

### 2.2 软件与材料

| 材料 | 用途 | 备注 |
|---|---|---|
| Kirin-Tool v2.4.2 | 参考其 dload/XLOADER 处理逻辑 | 它的软件 testpoint 对 `ONLINE_UPDATE` 包会失败 |
| PotatoNV-next v2.2.1 + `bootloaders/hisi65x_a` | 临时 USB bootloader（xloader + fastboot） | GPLv3；bootloader 镜像是华为财产，不要分发 |
| huawei-usbdload-tool | 5% USB Update 发送器 | 上游许可证需自行确认；本文不重复分发其代码 |
| 匹配的 OTA `update-377.zip` / `UPDATE.APP` | 原厂分区和 dload 包 | 必须与设备版本匹配；校验 MD5/SHA256 |
| Huawei DBAdapter 驱动（`hw_cdcacm` / `ew_usbccgpfilter`） | 5% 模式的 `DBAdapter Reserved Interface` COM | 只需要给 5% 模式用 |
| pyusb + libusb-package | VCOM/裸 fastboot | Windows 上用 libusb 后端，不需要 COM 驱动 |
| Magisk 25.2（可选） | root | GPLv3；本文未执行 root |
| TWRP `twrp-3.4.0-0-prague.img`（仅诊断） | ADB/dd/读日志 | **这是 P8 Lite 2017 的 TWRP，不是 nova 2 (PIC/Picasso)**；用完恢复原厂 recovery |

### 2.3 Python 环境

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install pyserial crccheck pyusb libusb-package
# 可选：HEIC 截图转换
.\.venv\Scripts\python.exe -m pip install pillow-heif
```

### 2.4 本文仓库里的脚本

| 脚本 | 作用 |
|---|---|
| `analysis/vcom_upload.py` | pyusb 直传 PotatoNV 的 Kirin 65x bootloader 到 VCOM |
| `analysis/fastboot_nve.py` | 裸 fastboot，发送二进制 `getvar:nve:` 写入/读取 |
| `analysis/extract_more_parts.py` | 从 `UPDATE.APP` 提取 cache/system/vendor/odm/product |
| `analysis/extract_parts_own.py` | 提取 XLOADER/KERNEL/RAMDISK/RECOVERY_RAMDISK/VBMETA |
| `analysis/dump_part.py` | 通过 TWRP ADB 读取 oeminfo/dfx 诊断 |
| `analysis/updateapp-parts.txt` | `UPDATE.APP` 分区偏移/大小 |

5% 发送器和 dload 解包器来自上游 huawei-usbdload-tool；如果公开仓库，建议**链接上游**而不是复制其代码（除非确认许可证允许）。

### 2.5 关键文件哈希（本次 377 包，示例）

| 文件 | SHA256 |
|---|---|
| 原厂 `XLOADER.img` | `5A796B3A09F38164705590F1C685BEE2EADA56154C872C1D625382FBF98F8643` |
| `KERNEL.img` | `9864D05E5E42BC2A3CDAB55B557F3966D0FEFBE09B0E860E11928791331DA5BD` |
| `RAMDISK.img` | `C70BA8CEE323AA54318CF053253C96CC8C7CD96C40AE9CD6E71E99B36E5DE261` |
| `RECOVERY_RAMDISK.img` | `ACE76FCD350D3C86EF3FAE556D68AF9C7A60184134AD1DB88ECAE9F5292E517D` |
| `VBMETA.img` | `1ED2BDED94399ACEFD537B1154DAC142B2C64D26BB030E5227F38A84AB7BD411` |
| `RECOVERY_VBMETA.img` | `452F597C13EF123950FBABE5EE53405082C983F47F1D39AAF62D9D92F0F40D55` |
| Magisk 25.2 APK | `0BDC32918B6EA502DCA769B1C7089200DA51EA1DEF170824C2812925B426D509` |
| TWRP prague（仅诊断） | `0620F8454CFF7F0EA3CD61450FC8021AD50D81E6D413C5AC1D028ADD5DE9FA0C` |

哈希只用于校验材料；不要把它们当成跨版本通用值。

---

## 3. 准备固件

1. 用 Firmware Finder 或官方渠道找到**与设备完全匹配**的 OTA。本次是 `PIC-TL00 8.0.0.377(C01)`。
2. 下载 `update-377.zip`，核对官方 filelist 的 MD5。本次包 1,915,377,768 字节，MD5 `5EC1884EB11E4958A1ECA4131E0D5E74`。
3. 解出 `UPDATE.APP`（本次 3,992,312,976 字节）。
4. 用 `usbd-appupk.py` 或 `analysis/extract_parts_own.py` 提取分区。先提取并校验：
   - `XLOADER.img`（69,568 字节）
   - `KERNEL.img`（25,165,824）
   - `RAMDISK.img`（16,777,216）
   - `RECOVERY_RAMDISK.img`（33,554,432）
   - `VBMETA.img` / `RECOVERY_VBMETA.img`
5. 记录 `analysis/updateapp-parts.txt` 里的偏移；后续全量恢复可能要用。

> 为什么不能直接用官方 Kirin-Tool 的 software testpoint？  
> 它只接受离线/服务版 Base 包；我们的 OTA 是 `ONLINE_UPDATE`，会报 `Failed to Software Testpoint... Make sure you are using the Base UPDATE...`。所以我们自己做一个离线化 dload 包。

---

## 4. 5% USB Update + 离线化 dload

### 4.1 进入 5% 模式

1. 关机。
2. 同时按住 **音量上 + 音量下 + 电源**。
3. 出现 **USB 图标 + 5%** 后松手，连接 USB。

### 4.2 安装 DBAdapter 驱动

设备管理器中应出现 `DBAdapter Reserved Interface (COMx)`。如果没有：

- 安装 Huawei DBAdapter 驱动包里的 `hw_cdcacm.inf` 和 `ew_usbccgpfilter.inf`。
- 重新进入 5% 模式。
- 在设备管理器确认 `DBAdapter Reserved Interface` 的 COM 号。

> VCOM 阶段不需要这个 COM 驱动；那是 pyusb 直接访问 vendor bulk 接口。

### 4.3 dload 包结构

一个可以工作的最小包（只写到 XLOADER）：

```text
dload/
  SHA256RSA.img + .header
  CRC.img + .header
  CURVER.img + .header
  VERLIST.img + .header
  PACKAGE_TYPE.img + .header
  EFI.img + .header
  XLOADER.img + .header
  unlockcode
  list.txt
```

`list.txt` 每行 `分区名 1`；到 XLOADER 后停止（后面的分区不要让 5% 模式继续写）。

### 4.4 三个关键改动

**A. `PACKAGE_TYPE` -> `OFFLINE_UPDATE` + CRC 碰撞**

OTA 原始值是 `ONLINE_UPDATE`。把它改成 `OFFLINE_UPDATE`，并用一个 CRC 碰撞文件（本文称 `pk_cracked.bin`）让 update-binary 的 CRC 校验仍然通过。不要手写随机字节；用已经验证过的碰撞文件。

**B. XLOADER 前 0x8000 做 XOR**

用官方 `fastboot/payload` 的 0x8000 块（本文称 `crc_hacked.bin`）与 `XLOADER.img` 的前 0x8000 做 XOR：

```text
patched[0:0x8000] = crc_hacked[0:0x8000] XOR original_xloader[0:0x8000]
patched[0x8000:]  = original_xloader[0x8000:]
```

这样前 0x8000 的内容变了，但 CRC16-X25 与原始块一致。update-binary 接受它，设备重启后这个损坏的 XLOADER 会崩到 VCOM。

**C. XLOADER header 名字保持 `XLOADER`**

我们实测把 header 里的名字改成 `PRELOADER` 会被设备拒绝；保持 `XLOADER` 才能成功。不同 EMUI 版本可能不同，本文只适用于本次 8.0.0.377。

`unlockcode` 从 XLOADER header 的 12..20 字节取；本次是 `48 57 37 78 32 37 ff ff`（ASCII `HW7x27` + `ff ff`）。

### 4.5 发送

用上游 `usbdload.py`（本文不复制其代码；请从 huawei-usbdload-tool 获取并确认许可证），工作目录指向包含 `dload/` 的目录：

```powershell
Set-Location <包含 dload 的目录>
# <path-to-upstream> 指向你下载的 huawei-usbdload-tool
"1" | & <repo>\.venv\Scripts\python.exe <path-to-upstream>\usbdload.py
```

脚本会：

1. 找 `DBAdapter Reserved Interface` COM 口；
2. 握手；
3. 发送 unlock 命令；
4. 逐个发送 `list.txt` 里的镜像；
5. 发送 reboot / force-reboot，自动重启。

**预期：** 手机黑屏，Windows 出现 `USB SER` / `12D1:3609`。这就是 VCOM/bootrom。

**如果失败：**
- `HandShake Failed`：COM 口不对/驱动没装好/没有在 5% 模式。
- 某个分区 `Failed!`：CRC/PACKAGE_TYPE/XLOADER 补丁不对，或包版本不匹配。不要反复盲试。
- 如果手机还能正常启动，说明 XLOADER 没写进去；重新检查 dload 包。

---

## 5. VCOM：pyusb 上传临时 bootloader

VCOM 是 **vendor-specific bulk 接口**，不是 CDC ACM：

```text
12D1:3609  interface 0  class 0xff/0xff/0xff
  EP 0x01 OUT (bulk, 64 bytes)
  EP 0x81 IN  (bulk, 64 bytes)
```

不需要 COM 驱动，也不需要关 Secure Boot/开测试签名。本文用 `pyusb` + `libusb-package`。

### 5.1 帧格式（PotatoNV）

```text
head: FE 00 FF 01 | length BE32 | address BE32 | crc BE16
data: DA | seq | ~seq | payload(<=0x400) | crc BE16
tail: ED | seq | ~seq | crc BE16
```

- CRC 是 CCITT/XMODEM 表算法，初值 0，处理完数据后再处理两个 0 字节，大端写入。
- 每个 head/data 帧后设备回 1 字节 `0xAA`；tail 可能不回复。
- `vcom_upload.py` 已实现这些细节，并校验 PotatoNV 的 SHA1。

### 5.2 镜像和地址

`hisi65x_a/manifest.xml`：

```text
xloader.img   -> 0x00020000
fastboot.img  -> 0x10000000
```

```powershell
& <repo>\.venv\Scripts\python.exe <repo>\analysis\vcom_upload.py
```

成功后设备变成 `18D1:D00D` 临时 fastboot，产品名 `Fastboot2.0`。

```powershell
fastboot devices
fastboot oem lock-state info
# 预期：FB LockState: UNLOCKED
#       USER LockState: LOCKED
```

> 这个临时 bootloader 是 **FB UNLOCKED**，所以它能做 normal bootloader 不允许的事：`erase misc`、`oem reboot-recovery`、刷 vendor/odm/product 等。不要把它当成长期 recovery。

---

## 6. 写 NVME 解锁码（最关键的一步）

### 6.1 先备份

在写之前，用 `fastboot_nve.py` 读一次当前值：

```powershell
python analysis\fastboot_nve.py --read WVLOCK --read USRKEY
```

把输出保存到**私有**笔记里（不要提交）。我们读到的 WVLOCK 是占位符，USRKEY 是 32 字节 SHA256。

### 6.2 选一个 SHA256 不含 `0x00` 的 16 位码

`fastboot getvar:nve:` 的解析按 C 字符串处理；**USRKEY 里只要出现 `0x00`，写入就会被截断**。本次第一次写入的码 SHA256 里正好有 `0x00`，读回只有 14 字节，导致 `oem unlock` 无法匹配。

用脚本生成/扫描：

```python
import secrets, string, hashlib
alphabet = string.ascii_uppercase + string.digits
while True:
    code = ''.join(secrets.choice(alphabet) for _ in range(16))
    digest = hashlib.sha256(code.encode()).digest()
    if b'\x00' not in digest:
        print(code, digest.hex())
        break
```

或者自己生成 16 位码并检查。**不要把真实解锁码写进公开仓库。**

### 6.3 写入并校验

```powershell
python analysis\fastboot_nve.py --write-key <YOUR16CHARCODE> --verify-key <YOUR16CHARCODE>
```

预期：

```text
write WVLOCK: OKAY set nv ok
write USRKEY: OKAY set nv ok
WVLOCK: ... ascii='<YOUR16CHARCODE>'
USRKEY: ... len=33 ...
verify: OK
```

`USRKEY` 读回通常是 `32 字节 + 结尾 NUL`（len=33）；如果只有 15/17 字节，说明又被 NUL 截断了，换码重写。

NVME 里写的是：

- `WVLOCK` = 16 字节 ASCII 解锁码
- `USRKEY` = SHA256(解锁码) 的 32 字节

---

## 7. 恢复 stock XLOADER 并解锁

**顺序非常重要：先恢复原厂 XLOADER，再重启。**

在临时 fastboot 里：

```powershell
fastboot flash xloader <parts>\XLOADER.img
fastboot reboot-bootloader
```

如果忘了这一步，重启后手机会再次进入 VCOM；不是变砖，但要重新走 5% → VCOM。

然后正常 bootloader（`FB LOCKED`，`USER LOCKED`）：

```powershell
fastboot oem get-build-number
fastboot oem lock-state info
fastboot oem unlock <YOUR16CHARCODE>
```

手机上会出现：

```text
Unlock bootloader?
  Yes / Unlock bootloader (may void warranty)
  No  / Do not unlock bootloader and return
```

按音量键选 **Yes**，按电源键确认。手机会清空数据并尝试 factory reset。

验证：

```powershell
fastboot oem lock-state info
# USER LockState: UNLOCKED
```

> 如果解锁后 factory reset 失败、进入 eRecovery，不要重复 `oem unlock`；按第 8 节处理。

---

## 8. 解锁后的 boot loop / eRecovery（本次最大的坑）

### 8.1 症状

- 解锁确认后显示 `Your device has been unlocked and can't be trusted...`
- 然后进 eRecovery：`Data partition severely corrupted` / `恢复出厂设置失败`
- eRecovery 的 `Download latest version and recovery` 报 `获取软件包信息失败`（华为服务器已不提供老包）
- 用 5% 全量 377 dload 重刷 31 个分区后，仍然 eRecovery
- 刷 system/vendor/odm/product、kernel/ramdisk/vbmeta、清零 userdata、清 `bootfail_info`/`misc`，都没有解决

### 8.2 我们读到的关键证据

`bootfail_info`（mmcblk0p48）是 XIFB 结构：

```text
58 49 46 42 | 14 00 00 00 | 0f 00 00 00 | 00 10 00 00 ...
X  I  F  B                count=15
```

`dfx` 日志里有：

```text
oeminfo: ERROR: oeminfo index 331 not find.
oeminfo: ERROR: oeminfo index 94 not find.
preboot: check_unlock_misc_info: NO misc value, go to next mode!
```

这些说明解锁/factory reset 过程中 oeminfo 的部分项和 misc 状态被清掉，但它们不是唯一原因。

TWRP 的日志暴露了真正的问题：

```text
Can't probe device /dev/block/mmcblk0p53
Failed to mount '/cust' (Invalid argument)
```

`/cust` = **mmcblk0p53**，393,216 扇区 = 192 MB；它的 ext4 superblock（偏移 1024）全是 0。`UPDATE.APP` 的 31 个分区里**没有 CUST**，所以全量 dload 也不会修它。系统 init 在挂载 `/cust` 失败后进入 eRecovery；factory reset 也因为它失败。

### 8.3 修复

用 TWRP（只作为临时 ADB/dd 工具）：

```powershell
adb shell "mke2fs -t ext4 -F -L cust /dev/block/bootdevice/by-name/cust"
adb shell "mount -t ext4 /dev/block/bootdevice/by-name/cust /cust"
adb shell "mount | grep cust"
```

预期：

```text
/dev/block/mmcblk0p53 on /cust type ext4 (rw,...)
```

然后恢复原厂 recovery，重启：

```powershell
adb push <parts>\RECOVERY_RAMDISK.img /cache/recovery_stock.img
adb shell "dd if=/cache/recovery_stock.img of=/dev/block/bootdevice/by-name/recovery_ramdisk bs=1048576"
adb shell "sync"
adb reboot
```

本次执行后系统成功启动。

> `/cust` 现在是空 ext4；运营商定制内容缺失。基础功能正常，但个别运营商定制应用/主题可能没有。要完全恢复 CUST 需要完整服务固件。

### 8.4 不要做的事

- 不要把 `twrp-3.4.0-0-prague.img` 当 nova 2 的长期 TWRP：它是 **P8 Lite 2017** 的。可以临时用 ADB/dd，但用完恢复原厂 recovery。
- 不要因为 eRecovery 循环就反复 `oem unlock`/factory reset；每次都会增加 bootfail 计数。
- 不要在没有备份的情况下清 `oeminfo`、`frp`、`secure_storage` 或写随机镜像。
- 不要在 normal bootloader 上浪费时间试 `fastboot boot` / `oem reboot-recovery` / `erase misc` / `erase metadata` / `flash vendor`：FB LOCKED 会返回 `Command not allowed`，需要用 FB UNLOCKED 临时 bootloader。

### 8.5 可选：清 bootfail_info/misc

如果确认需要（例如计数很高、misc 有残留），在 FB UNLOCKED 临时 bootloader 或 TWRP 里做：

```powershell
# TWRP：
adb shell "cat /sys/class/block/mmcblk0p48/size"   # 512-byte sectors
adb shell "dd if=/dev/zero of=/dev/block/bootdevice/by-name/bootfail_info bs=512 count=<sectors>"
adb shell "dd if=/dev/zero of=/dev/block/bootdevice/by-name/misc bs=1048576 count=1"
```

这次清了 `bootfail_info`/`misc` 并没有单独解决 boot loop；真正原因是 `/cust`。不要把它们当成万能修复。

---

## 9. 解锁后的检查

```powershell
fastboot oem lock-state info
# USER LockState: UNLOCKED

adb shell getprop ro.boot.flash.locked
# 0

adb shell getprop ro.boot.verifiedbootstate
# orange
```

- 开机出现 `Your device has been unlocked and can't be trusted` 是正常的；不要因此重新上锁。
- 数据已清空；`/cust` 是空 ext4。
- 解锁状态下部分银行/支付 App 可能拒绝；OTA 可能受影响。
- **不要随意 `fastboot oem lock`**：重新上锁可能清数据，甚至在系统状态不一致时变砖。

### 可选 root（本次未执行）

本文只验证到解锁和系统启动。若以后要 root，标准流程是：

1. 用原厂 `RAMDISK.img`（必须与当前系统版本匹配）在手机 Magisk App 里 patch；
2. `adb pull` 出 `magisk_patched-*.img`；
3. `adb reboot bootloader`;
4. `fastboot flash ramdisk magisk_patched-*.img`;
5. `fastboot reboot`;
6. `adb shell su -c id` 验证。

不要用与系统版本不匹配的 RAMDISK；不要在未确认分区名/AVB 状态时乱刷。

---

## 10. 踩坑清单

1. **Kirin-Tool 官方软件 testpoint 不接受 `ONLINE_UPDATE`**；必须离线化 dload。
2. **XLOADER header 名字不要改成 `PRELOADER`**；本次 EMUI 8 会拒绝，保持 `XLOADER`。
3. **5% 模式需要 DBAdapter COM 驱动**；VCOM 不需要，pyusb 直接 bulk。
4. **不要用 Zadig 绑键盘/鼠标/摄像头**；我们误绑过 A4Tech 键盘，`pnputil /delete-driver ... /uninstall /force` 才恢复。只对目标设备操作。
5. **PotatoNV 的 Target device 为空不是 bug**：它要 COM 串口；VCOM 是 vendor bulk，所以用本文的 pyusb 上传器。
6. **`fastboot boot`、`oem reboot-recovery`、`erase misc`、`erase metadata`、`flash vendor/odm/product` 在 normal bootloader（FB LOCKED）都会被拒**；临时 PotatoNV bootloader（FB UNLOCKED）可以。
7. **`USRKEY` 会被 NUL 截断**：16 位码的 SHA256 里不能有 `0x00`；写完必须 `--verify-key` 读回 33 字节（32+SHA+NUL）。
8. **重启前必须恢复原厂 XLOADER**；否则回 VCOM。
9. **全量 377 dload 会把 USER 重新锁上**；之后用同一解锁码重新 `oem unlock`。
10. **`twrp-3.4.0-0-prague.img` 是 P8 Lite 2017 的**，不是 nova 2 (PIC/Picasso)；只能临时用于 ADB/dd/读日志。
11. **eRecovery 的 `Download latest version` 可能失败**：`获取软件包信息失败`，因为服务器没有老包；用本地 377 包。
12. **`UPDATE.APP` 不含 CUST**；`/cust` 空/未格式化会导致系统 eRecovery 循环，`mke2fs -t ext4` 是这次的决定性修复。
13. **`bootfail_info`/`misc` 清零不一定能修 boot loop**；它们只是计数器/启动命令，别把希望全押在这里。
14. **`oeminfo index 331/94/92 not find` 在 dfx 里出现**，但不要在没有备份时乱改 oeminfo；本次不是决定性原因。
15. **不要在公开仓库放 SN/IMEI/解锁码/固件/bootloader**；这些是隐私/版权材料。

---

## 11. 开源与许可证注意事项

- **设备隐私**：SN、IMEI、解锁码、`oeminfo`/`dfx` dump、日志、截图都可能包含设备信息；公开前必须清理/替换为占位符。
- **固件/ bootloader**：华为固件和 PotatoNV 的 bootloader 镜像是华为财产；不要在公开仓库重新分发。让用户从官方/上游下载并自行校验。
- **第三方代码**：
  - Kirin-Tool 的源码是 **Read-Only Reference License**；不要复制/再分发。
  - PotatoNV 是 **GPLv3**；如果包含其代码，仓库需要兼容 GPL。
  - TWRP、Magisk 是 **GPLv3**；不要打包镜像/代码而不遵守许可证。
  - huawei-usbdload-tool 的许可证需自行确认；最稳妥是链接上游，不复制。
- **本文原创文本/脚本**：**MIT**（见仓库根目录 `LICENSE`）。第三方组件保留各自许可证。
- **合规**：只用于自有设备、学习/研究/维修；遵守当地法律；不提供解锁服务。

---

## 附录 A：协议要点

### A.1 5% USB Update（DBAdapter COM）

- HDLC：`0x7E` 帧边界；转义 `0x7D 0x5E`（0x7E）、`0x7D 0x5D`（0x7D）。
- CRC16-X25，小端。
- 手写命令：`0x0B` unlockcode、`0x41` head、`0x0F` data、`0x43` tail、`0x0A` reboot、`0x32` force reboot。
- 数据块 zlib 压缩；`list.txt` 控制分区顺序。

### A.2 VCOM（12D1:3609）

- 帧/CRC/ACK 见第 5 节。
- CRC：`binascii.crc_hqx` 表算法，初值 0，末尾两个 0 字节。
- `xloader.img` @ 0x00020000；`fastboot.img` @ 0x10000000。

### A.3 临时 fastboot（18D1:D00D）

- 接口 class `0xff/0x42/0x03`；EP `0x01` OUT / `0x81` IN。
- `getvar:nve:<PROP>@<binary>` 写 NVME；`getvar:nve:<PROP>` 读。
- 读回值末尾通常带 NUL；比较时 `rstrip(b"\x00")`。

---

## 附录 B：来源

- Firmware Finder 数据：<https://github.com/felpcereti/Huawei-Firmware-Finder>
- 开源 USB DLOAD：<https://github.com/kasnria001/huawei-usbdload-tool>
- PotatoNV：<https://github.com/mashed-potatoes/PotatoNV>
- PotatoNV cross-platform：<https://github.com/mashed-potatoes/PotatoNV-crossplatform>
- Kirin-Tool：<https://kirintool.cfd/>
- Linux USB update detection：<https://github.com/Redminote11tech/kirin-tool-linux/blob/main/docs/usb-update-linux-detection.md>

---

## 最后

如果你按这个流程成功或遇到新问题，欢迎提交 issue/PR，附上**脱敏**后的日志和版本信息。不要在公开 issue 里贴 SN/IMEI/解锁码或完整固件。
