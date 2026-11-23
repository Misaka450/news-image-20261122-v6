# v6 规格与 26 条素材表 — Sunday 22 November 2026

> 核心策略：**砍信息量，换插画覆盖率与清晰度预算**。从 v5 的 34 条压缩为精选 26 条，实现 **100% 故事插画覆盖（14 张主卡大插画 + 12 条简讯 24×24px 线描图标）**，全面采用冠军 `r01` 的暖报纸底色 `#F8F3E9`、无厚边框开放排布与底部大留白呼吸区。
> 全程纯 Python + Pillow 确定性绘制，1024×1024 原生像素，≤1,048,576 字节，两次运行 MD5 完全一致。

## 1. 版式架构（1024×1024 原生像素，区块间距统一 10px，卡内边距 8px）

| 区域 | Y 区间 | 高度 | 规格说明 |
|---|---|---|---|
| 1. 顶部细条 | `0..20` | 20px | 全宽深海军蓝 `#101D3D`，左 `THE WORLD IN ONE DAY`（金色），右 `26 STORIES · 7 REGIONS · EVERY ONE DATED SUNDAY 22 NOVEMBER 2026`（白色） |
| 2. 超大红字日期报头 | `22..72` | 50px | `Sunday 22 November 2026`（~54px 猩红粗衬线 `#9E1F28` 居中留白）+ `74..77` 双色编辑饰线（2px 深墨 + 1px 猩红） |
| 3. 6 格大数字条 | `80..128` | 48px | 无外框开放 6 等宽格（细竖分割线），38–40px 猩红粗衬线共享基线数字 + 9–10px 大写标签；全部由 `STORIES` 正则提取校验 |
| 4. DAY IN UTC 时间轴 | `133..155` | 22px | 深蓝单行带 `#162647`，左标 `DAY IN UTC`，右 6 个单行等宽关键 UTC 时刻（金色时刻 + 白色摘要，零折行） |
| 5. 7 色区域条 | `160..178` | 18px | 7 区实色分段，内嵌 `区域名 + 计数`（动态统计，3–4 条/区） |
| *(呼吸留白)* | `178..188` | 10px | 统一 10px 区块间隙 |
| 6. 14 张主卡区（4 行：3+3+4+4） | `187..665` | 478px | 每行高 `112px`，行距 `10px`，列距 `10px`；无厚外框直落报纸底色，顶部 2px 区域色条，**全部 14 卡带高 `110px` 线描+平涂插画**（#1–#6 为 `110×110px`，#7–#14 为 `68×110px`），固定节奏：**19px 粗衬线标题（≤2 行）+ 12px 导语（≤2 行）+ 9px 来源（1 行）** |
| *(呼吸留白)* | `666..676` | 10px | 统一 10px 区块间隙 |
| 7. 下半部：左地图 + 右 12 条带图标简讯 | `676..896` | 220px | 上下严格对齐：`x=14..334` 为 **320×220** 深海蓝极简世界地图（标示 #15–#26 共 12 枚防碰撞编号钉）；`x=344..1010` 为 **2 栏×6 行共 12 条简讯**，每条左侧 **24×24px 独立线描图标** + 右侧 2 行文字，无边框、无状态药丸噪点 |
| 8. 底部呼吸区（`y=896..1024`） | `896..1024` | 128px | 彻底清除堆叠：`896..912` 留白 16px + `912..954`（42px）`DATE CHECK — READ THIS FIRST` 声明（含剔除清单，≤2 行）+ `954..988` 留白 34px + 双色编辑底线 + `994..1012`（18px）单行页脚（日期 + 26 条故事 + 生成方式）+ `1012..1024` 底边距 12px；内容块总高 60px（≤70px） |

## 2. 6 格关键数字条（全部由 26 条素材真实正则提取）

| 数值 | 标签 | 对应故事 | 核验依据（2026-11-22 当日） |
|---|---|---|---|
| `186` | DRONES AT UKRAINE | #2 | 俄军 11 月 22 日夜间向乌克兰发射 186 架无人机 |
| `161` | DRONES DOWNED | #2 | 乌方防空与电子战击落或压制 161 架 |
| `$120bn` | COP31 FINANCE FLOOR | #1 | COP31 谈判破裂核心分歧：1200 亿美元/年适应资金下限被删 |
| `74,742` | GAZA DEATH TOLL | #12 | 加沙卫生部门 11 月 22 日更新累计死亡人数 |
| `856` | HK POLL CANDIDATES | #5 | 香港选举委员会界别分组一般选举 856 名候选人竞逐 723 席 |
| `720/9` | INDIA TEST RECORD | #8 | 印度在惠灵顿测试赛以 720/9 宣告结束创客场新西兰纪录 |

## 3. DAY IN UTC 时间轴（6 个单行关键时刻）

1. `01:00` — HK polls open (#5)
2. `01:25` — Cartel chief seized (#7)
3. `03:00` — COP31 talks fail (#1)
4. `04:00` — Vegas F1 GP (#21)
5. `10:44` — Mercury orbit (#6)
6. `20:43` — Alcaraz ATP (#11)

## 4. 7 区域均衡分布（总计 26 条，每区 3–4 条）

| 区域 | 条数 | 主卡（14） | 简讯（12） |
|---|---|---|---|
| EUROPE | 4 | #2, #10, #11 | #15 |
| ASIA-PACIFIC | 4 | #5, #9 | #18, #19 |
| AMERICAS | 4 | #7, #13 | #20, #21 |
| MIDDLE EAST | 4 | #4, #12 | #16, #17 |
| AFRICA | 4 | #3, #14 | #22, #23 |
| OCEANIA | 3 | #8 | #24, #25 |
| WORLD | 3 | #1, #6 | #26 |
| **合计** | **26** | **14 张主卡** | **12 条简讯** |

## 5. 精选 26 条 2026-11-22 真实国际新闻素材表

### 主卡区（#1–#14，14 张主卡，全部配备 110px 高线描插画）

| # | 区域 | 领域 | 标题 | 导语 | 来源媒体 | 插画主题 |
|---|---|---|---|---|---|---|
| 1 | WORLD | CLIMATE | COP31 collapses in Antalya | Nearly 200 nations deadlock past 03:00 UTC over fossil fuels and a $120bn floor. | Reuters, AFP, BBC | 裂纹地球与倾斜木槌 |
| 2 | EUROPE | MILITARY | Russia fires 186 drones; 161 downed | Overnight wave of 72 jet UAVs batters Dymer flats and cuts power grids. | Ukr. Air Force, BBC | 雷达扫描与三角翼拦截 |
| 3 | AFRICA | MILITARY | Warship Merkury sinks in Benghazi | Russian corvette capsizes after suspected sea-drone strike off Libya. | Reuters, Al Jazeera | 倾覆军舰与海浪火羽 |
| 4 | MIDDLE EAST | MILITARY | Iran strike hurts 2 in Bahrain | Manama cites Sitra plant fire; IRGC alleges US Patriot radar hit. | MEE, Times of Israel | 炼油储罐烟柱与雷达 |
| 5 | ASIA-PACIFIC | POLITICS | HK polls hit 98.8% with 856 hopefuls | Election Committee fills 723 seats as 5,640 electors vote 01:00–10:00 UTC. | info.gov.hk, China Daily | 投票箱与勾选选票 |
| 6 | WORLD | SPACE | BepiColombo reaches Mercury | European-Japanese probe enters orbit after 8 yrs to map crust and field. | BBC, ESA | 陨坑水星与轨道探测器 |
| 7 | AMERICAS | SECURITY | Mexico seizes cartel chief | Special forces nab FBI Most Wanted boss Meza Flores in raid. | BBC, Reuters | 山脉剪影与探照直升机 |
| 8 | OCEANIA | SPORT | India hits record 720/9 | Visitors break NZ Test mark; hosts bat 120 overs to draw. | ESPN, Jamaica Obs. | 板球三柱门与球棒弧线 |
| 9 | ASIA-PACIFIC | DISASTER | Banten plant fire kills 3 | Rescuers comb gutted Banten factory; 36 missing, 4 hurt. | AFP, BBC | 锯齿厂房与火焰烟柱 |
| 10 | EUROPE | POLITICS | Fico blocks €45bn EU loan | Slovak PM rejects European Union aid package for Ukraine. | Reuters, Kyiv Post | 欧元徽记与红色否决线 |
| 11 | EUROPE | SPORT | Alcaraz wins ATP Finals | Spaniard beats Zverev in Turin for his first Finals title. | Reuters, Guardian | 网球场线球拍与奖杯 |
| 12 | MIDDLE EAST | CRISIS | Gaza toll hits 74,742 | Health ministry updates toll; Hamas urges mediator talks. | WAFA, Anadolu | 暮色天际线剪影 |
| 13 | AMERICAS | SPORT | Wembanyama drops 50 pts | Spurs star posts historic 50-pt, 19-reb night in Texas. | CBS, KSAT | 篮板篮筐与篮球弧线 |
| 14 | AFRICA | CONFLICT | Drones strike Khartoum sites | RSF UAVs hit residential homes and UN compound; four killed. | Al Jazeera | 城市屋顶与无人机预警 |

### 带图标简讯区（#15–#26，12 条简讯，全部配备 24×24px 线描图标及左下地图定位）

| # | 区域 | 坐标 (lon, lat) | 标题（第 1 行） | 地点与来源（第 2 行） | 24×24 线描图标 |
|---|---|---|---|---|---|
| 15 | EUROPE | (-2.2, 53.5) | 12,000 evacuated at Co-op Live arena | Manchester · Suspected gas alert · BBC, SBS | 场馆穹顶与疏散箭头 |
| 16 | MIDDLE EAST | (35.5, 33.9) | Lebanon marks 83rd Independence Day | Beirut · Locals return for holiday · NPR, L'Orient | 雪松树线描徽标 |
| 17 | MIDDLE EAST | (46.7, 24.7) | Saudi coalition intercepts Houthi fire | Riyadh · Missiles & UAVs downed · Anadolu, ISW | 防空盾牌与偏转轨迹 |
| 18 | ASIA-PACIFIC | (127.0, 37.6) | S. Korea education chief quits over AI | Seoul · Exam chaos forces exit · AFP, BBC | 试卷与芯片火花 |
| 19 | ASIA-PACIFIC | (127.7, 26.2) | Japan marks Shuri Castle hall rebuild | Okinawa · 7 yrs after fire · Wash. Post, JT | 冲绳城楼飞檐 |
| 20 | AMERICAS | (-53.8, -29.1) | Supercell storm kills 5, hurts 250+ | Tupanciretã, Brazil · Severe hail · AFP | 龙卷风漏斗与闪电 |
| 21 | AMERICAS | (-115.1, 36.2) | Verstappen wins Las Vegas F1 GP | Las Vegas · Beats both McLarens · Guardian | 格子旗与赛车轮 |
| 22 | AFRICA | (6.1, 4.8) | Boat capsize kills 24 mourners | Bayelsa, Nigeria · River tragedy · AllAfrica | 倾斜木船与波浪 |
| 23 | AFRICA | (15.9, -1.2) | Kenya's Ruto & DRC restore full ties | Oyo, Congo · Summit accord · Pan African Visions | 双环外交连结 |
| 24 | OCEANIA | (149.1, -35.3) | Albanese backs Bowen after COP31 | Canberra · Defends climate envoy · Guardian AU | 议会讲台与麦克风 |
| 25 | OCEANIA | (147.2, -9.4) | Pope urges aid for PNG drought | Port Moresby · All 22 zones hit · Crux, CathNews | 烈日与水滴 |
| 26 | WORLD | (6.1, 46.2) | WTO flags $1.5tn export, $5.4tn curbs | Geneva · Record trade barriers · WTO, SunStar | 集装箱与关税壁垒线 |

## 6. DATE CHECK 主动剔除清单（反伪证）

- **Peru M6.7 earthquake**（Fri 20 Nov 2026）
- **Russia's 400-drone barrage**（Thu 19–Fri 20 Nov 2026；11 月 22 日为 186 架）
- **APEC Shenzhen summit**（Thu 19 Nov 2026）
- **French Senate police bill vote**（Fri 20 Nov 2026）
