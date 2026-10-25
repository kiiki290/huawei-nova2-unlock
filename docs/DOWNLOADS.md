# 下载链接与分发说明

> 本仓库**只分发原创文档/脚本**（MIT），**不托管**华为固件、bootloader、专有驱动或第三方二进制。  
> 下面的链接指向官方或上游来源；版本/哈希用于校验。固件和 bootloader 是华为财产，第三方工具各有自己的许可证；请勿把本页内容理解为再分发授权。

## 1. 固件（必须与设备版本匹配）

本次测试设备：**PIC-TL00 / EMUI 8.0.0.377(C01)**，bootloader 构建 8.0.0.386(C01)。

| 项目 | 链接/来源 | 版本/大小 | 校验 |
|---|---|---|---|
| PIC-TL00 377 OTA 目录（华为 CDN，历史链接） | <http://update.dbankcdn.com/download/data/pub_13/HWHOTA_hotaMigrate_900_9/bd/v3/ca84a76c58bd4243a9797f3fae2ac574/> | `update-377.zip`；1,915,377,768 字节 | MD5 `5EC1884EB11E4958A1ECA4131E0D5E74`；SHA256 `6EFE27F466D633727303F5A57FE38B245826257053A5C167D36DE4223C823BA7` |
| Firmware Finder 数据 | <https://github.com/felpcereti/Huawei-Firmware-Finder> | 按型号/版本查找 | 以官方 filelist/包内哈希为准 |
| 本次 `UPDATE.APP` | 从 `update-377.zip` 解出 | 3,992,312,976 字节 | 见下方分区哈希 |
| 官网/服务固件 | 华为官方支持/售后渠道 | 以实际型号为准 | 官方校验 |

**注意：**

- 上面的华为 CDN 目录可能已经失效或只返回 403/404（我们复查时 `filelist.xml` 已是 404）。**不要把它当成长期可用镜像**；优先用 Firmware Finder 或可信的官方/服务渠道。
- 377 系统 + 386 bootloader 是我们这台设备的状态；不要把 377/386/其他版本的分区混刷。
- 网上“免费固件/一键解锁包”很多带修改或恶意文件；至少核对 MD5/SHA256，并确认来源。
- 不要使用与设备型号不符的固件（例如把 P8 Lite 2017 `prague` 的包刷到 nova 2 PIC）。

## 2. 工具

| 工具 | 链接 | 许可证/说明 |
|---|---|---|
| PotatoNV-next v2.2.1（Kirin 65x 临时 bootloader） | <https://github.com/mashed-potatoes/PotatoNV> · <https://github.com/mashed-potatoes/PotatoNV/releases/download/2022.03/PotatoNV-next-v2.2.1_2022.03-x86.zip> | GPLv3；`bootloaders/hisi65x_a` 里的 bootloader 镜像是华为财产，不要单独再分发 |
| huawei-usbdload-tool（5% USB Update 发送器） | <https://github.com/kasnria001/huawei-usbdload-tool> | 上游许可证需自行确认；本仓库不复制其代码 |
| Kirin-Tool v2.4.2 | <https://kirintool.cfd/> · <https://github.com/kethily-daniel/Kirin-Tool> | **Read-Only Reference License**：禁止复制/再分发；只作参考 |
| Android platform-tools（adb/fastboot） | <https://developer.android.com/tools/releases/platform-tools> | Google/Android SDK 条款 |
| Python 3.14 | <https://www.python.org/downloads/> | PSF License |
| pyserial | <https://pypi.org/project/pyserial/> | BSD |
| crccheck | <https://pypi.org/project/crccheck/> | MIT |
| pyusb | <https://pypi.org/project/pyusb/> | BSD |
| libusb-package | <https://pypi.org/project/libusb-package/> | BSD |
| Huawei Testpoint/DBAdapter 驱动（第三方分享） | <https://files.dc-unlocker.com/share.html?v=share/18B15B9D02C945A79B1967234CECB423> | 第三方/专有；来源和安全性自行确认 |
| HiSuite（官方驱动/恢复） | <https://consumer.huawei.com/en/support/hisuite/> | 华为专有；不要从随机镜像下载 |
| TWRP `prague`（仅诊断） | <https://dl.twrp.me/prague/> | GPLv3；**这是 P8 Lite 2017 的 TWRP，不是 nova 2 (PIC/Picasso)**；仅临时 ADB/dd |
| Magisk 25.2（可选 root） | <https://github.com/topjohnwu/Magisk/releases> | GPLv3；本仓库不打包 APK |
| Linux USB update 检测资料 | <https://github.com/Redminote11tech/kirin-tool-linux/blob/main/docs/usb-update-linux-detection.md> | 参考资料 |

### PotatoNV 说明

PotatoNV 的 README 明确：所有 bootloader 都是**加载到 RAM**；选错 bootloader 一般不会永久写坏设备。  
但 **拆机短接/测试点** 本身有硬件损坏风险；FBLOCK/Disable FBLOCK 选项在 Kirin 65x/960 上才相对可靠，不要在其他老设备上乱用。

### Kirin-Tool 说明

Kirin-Tool 的源码和打包物是 **Read-Only Reference License**，不允许再分发/修改/商用；本仓库只链接官网，不复制其代码。它的 software testpoint 面向的是较新的 Kirin（如 710/970/980），不是本次 65x 的主流路径。

## 3. 校验命令

Windows PowerShell：

```powershell
Get-FileHash .\update-377.zip -Algorithm SHA256
Get-FileHash .\update-377.zip -Algorithm MD5
certutil -hashfile .\update-377.zip SHA256
```

Linux/macOS：

```bash
sha256sum update-377.zip
md5sum update-377.zip
```

### 本次固件分区 SHA256（377 包示例）

| 分区 | SHA256 |
|---|---|
| `XLOADER.img`（原厂） | `5A796B3A09F38164705590F1C685BEE2EADA56154C872C1D625382FBF98F8643` |
| `KERNEL.img` | `9864D05E5E42BC2A3CDAB55B557F3966D0FEFBE09B0E860E11928791331DA5BD` |
| `RAMDISK.img` | `C70BA8CEE323AA54318CF053253C96CC8C7CD96C40AE9CD6E71E99B36E5DE261` |
| `RECOVERY_RAMDISK.img` | `ACE76FCD350D3C86EF3FAE556D68AF9C7A60184134AD1DB88ECAE9F5292E517D` |
| `VBMETA.img` | `1ED2BDED94399ACEFD537B1154DAC142B2C64D26BB030E5227F38A84AB7BD411` |
| `RECOVERY_VBMETA.img` | `452F597C13EF123950FBABE5EE53405082C983F47F1D39AAF62D9D92F0F40D55` |
| Kirin-Tool v2.4.2 zip | `DFB8E7FCE2F6FEF26FFCCAA9BC3B2B76A3C32F654B16FF784C906857AC298537` |
| Magisk 25.2 APK | `0BDC32918B6EA502DCA769B1C7089200DA51EA1DEF170824C2812925B426D509` |
| TWRP prague（仅诊断） | `0620F8454CFF7F0EA3CD61450FC8021AD50D81E6D413C5AC1D028ADD5DE9FA0C` |

## 4. 为什么只给链接，不直接分发

1. **版权/许可证**：华为固件、XLOADER/FASTBOOT、专有驱动、PotatoNV 的 bootloader 镜像都不是我们的；Kirin-Tool 的许可证明确禁止再分发。
2. **体积**：`update-377.zip` 1.9 GB、`UPDATE.APP` 3.99 GB；GitHub 不适合托管这种大二进制。
3. **安全/供应链**：让用户从官方/上游下载并校验哈希，比在本仓库放一份来源不明的二进制更安全。
4. **隐私**：设备 SN/IMEI、解锁码、`oeminfo`/`dfx`/NVME dump 不能公开。

如果你要自己做镜像/分发，请先确认对应许可证和版权；本仓库不提供再分发授权。  
本仓库原创内容（文档、脚本）是 MIT；第三方组件保留各自许可证。
