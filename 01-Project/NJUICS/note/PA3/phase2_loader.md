---

excalidraw-plugin: parsed
tags: [excalidraw]

---
==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠==


# Text Elements
AM编译的用户程序执行过程 ^s3NVkYoJ

ENTRY(_start)

SECTIONS {
  . = _pmem_start + 0x100000;
  .text : {
    *(entry)
    *(.text*)
  }
  etext = .;
  _etext = .;
  .rodata : {
    *(.rodata*)
  }
  .data : {
    *(.data)
  }
  edata = .;
  _data = .;
  .bss : {
	_bss_start = .;
    *(.bss*)
    *(.sbss*)
    *(.scommon)
  }
  _stack_top = ALIGN(0x1000);
  . = _stack_top + 0x8000;
  _stack_pointer = .;
  end = .;
  _end = .;
  _heap_start = ALIGN(0x1000);
}
 ^Iv4JYtyV

入口函数 ^2h6pZk9i

此时还是正常的elf文件，开头是elf头等一系列
信息，然后是text节等 ^vWh3q4oj

但对于直接运行在裸机上的程序来说，我们并不需要elf头
因此，我们通过 objcopy 命令去掉没有用的信息。  ^LkCiuhJS

此时二进制文件的text, data等也是从 0x0 开始 ^APr21oqy

这个命令是把我们的 xx.bin 文件加载到 nemu 中执行，在
NEMU中，我们通过load_img函数把 xx.bin 加载进来，并放到
合适的位置（IMAGE_START)处，因为 xx.bin 中的位置信息都是
基于 IMAGE_START 的，这也是am的脚本所规定的。 ^sLPU6rsu

然后让nemu的cpu.pc 指向IMAGE_START 的初始位置，就开始
状态机的执行过程：
取指
译码
执行 ^KTapuQSl

操作系统的用户程序执行过程 ^JgM1m01e

众所周知，操作系统也是一个程序，也是通过硬件执行的。
但它特殊在什么地方呢？ ^AdXohi2z

OS最重要的特点就是可以管理其他程序的执行 ^t58LRyv3

有了操作系统后，我们就可以实现一个永不停止的计算机了。
当一个程序运行完毕后，操作系统会自动加载另一个程序，
周而复始。 ^1Rh4kt74

可以看到，0x1000以内的是elf头，然后align=0x1000，从
0x2000开始就是text节了，但elf头中记录了virtual的虚拟
地址（也就是程序执行过程中所使用的地址）。 ^RpnA5CSZ

具体可以看CSAPP链接那一章，还有相对地址寻址的一些问题 ^rE1wNLdi


# Embedded files
6f4811c7bd9faf199a41c1a78fd1258c770f55d7: [[gKliRA.png]]
f790cb14c9e6cd814a6ef9b969b652b1cc719915: [[Pasted Image 20231019222625_949.png]]
bd14cd015dd5ec368d2ef73e6845a6aa51b0158e: [[Pasted Image 20231019222910_975.png]]
2bfee2a4efdc726671452e5bdd9fdc4a77fd4e9f: [[Pasted Image 20231019223914_293.png]]
b1d65c508c598b46a7268de97530be25e17a74ca: [[Pasted Image 20231019224303_384.png]]
31d8ae4ca8924eaf3ce1d066bfa5c6985aee224a: [[Pasted Image 20231019230421_747.png]]

%%
# Drawing
```json
{
	"type": "excalidraw",
	"version": 2,
	"source": "https://github.com/zsviczian/obsidian-excalidraw-plugin/releases/tag/1.9.24",
	"elements": [
		{
			"type": "text",
			"version": 127,
			"versionNonce": 1670843339,
			"isDeleted": false,
			"id": "s3NVkYoJ",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -289.629667161037,
			"y": -215.2770859483752,
			"strokeColor": "#1971c2",
			"backgroundColor": "transparent",
			"width": 438.9697265625,
			"height": 44.8527444943452,
			"seed": 1752625637,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697726738250,
			"link": null,
			"locked": false,
			"fontSize": 37.377287078621,
			"fontFamily": 4,
			"text": "AM编译的用户程序执行过程",
			"rawText": "AM编译的用户程序执行过程",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "AM编译的用户程序执行过程",
			"lineHeight": 1.2,
			"baseline": 34
		},
		{
			"type": "image",
			"version": 567,
			"versionNonce": 855887141,
			"isDeleted": false,
			"id": "0apnY8v6",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -462.30760127670555,
			"y": -74.06531217666304,
			"strokeColor": "#000000",
			"backgroundColor": "transparent",
			"width": 334.9764648437501,
			"height": 176.924189178037,
			"seed": 68649,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697726249341,
			"link": null,
			"locked": false,
			"status": "pending",
			"fileId": "6f4811c7bd9faf199a41c1a78fd1258c770f55d7",
			"scale": [
				1,
				1
			]
		},
		{
			"type": "text",
			"version": 173,
			"versionNonce": 821641142,
			"isDeleted": false,
			"id": "Iv4JYtyV",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -449.9849470755822,
			"y": 143.11129396610704,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 175.95703125,
			"height": 384.5043159026937,
			"seed": 834472939,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697880837161,
			"link": null,
			"locked": false,
			"fontSize": 10.013133226632648,
			"fontFamily": 3,
			"text": "ENTRY(_start)\n\nSECTIONS {\n  . = _pmem_start + 0x100000;\n  .text : {\n    *(entry)\n    *(.text*)\n  }\n  etext = .;\n  _etext = .;\n  .rodata : {\n    *(.rodata*)\n  }\n  .data : {\n    *(.data)\n  }\n  edata = .;\n  _data = .;\n  .bss : {\n\t_bss_start = .;\n    *(.bss*)\n    *(.sbss*)\n    *(.scommon)\n  }\n  _stack_top = ALIGN(0x1000);\n  . = _stack_top + 0x8000;\n  _stack_pointer = .;\n  end = .;\n  _end = .;\n  _heap_start = ALIGN(0x1000);\n}\n",
			"rawText": "ENTRY(_start)\n\nSECTIONS {\n  . = _pmem_start + 0x100000;\n  .text : {\n    *(entry)\n    *(.text*)\n  }\n  etext = .;\n  _etext = .;\n  .rodata : {\n    *(.rodata*)\n  }\n  .data : {\n    *(.data)\n  }\n  edata = .;\n  _data = .;\n  .bss : {\n\t_bss_start = .;\n    *(.bss*)\n    *(.sbss*)\n    *(.scommon)\n  }\n  _stack_top = ALIGN(0x1000);\n  . = _stack_top + 0x8000;\n  _stack_pointer = .;\n  end = .;\n  _end = .;\n  _heap_start = ALIGN(0x1000);\n}\n",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "ENTRY(_start)\n\nSECTIONS {\n  . = _pmem_start + 0x100000;\n  .text : {\n    *(entry)\n    *(.text*)\n  }\n  etext = .;\n  _etext = .;\n  .rodata : {\n    *(.rodata*)\n  }\n  .data : {\n    *(.data)\n  }\n  edata = .;\n  _data = .;\n  .bss : {\n\t_bss_start = .;\n    *(.bss*)\n    *(.sbss*)\n    *(.scommon)\n  }\n  _stack_top = ALIGN(0x1000);\n  . = _stack_top + 0x8000;\n  _stack_pointer = .;\n  end = .;\n  _end = .;\n  _heap_start = ALIGN(0x1000);\n}\n",
			"lineHeight": 1.2,
			"baseline": 382
		},
		{
			"type": "arrow",
			"version": 68,
			"versionNonce": 767090821,
			"isDeleted": false,
			"id": "Uh4-_uKI8k-Yx4YiJzjK2",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -372.08693560671327,
			"y": 148.25998070131365,
			"strokeColor": "#e03131",
			"backgroundColor": "transparent",
			"width": 137.6065545581912,
			"height": 10.068772284745705,
			"seed": 611874917,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1697726249341,
			"link": null,
			"locked": false,
			"startBinding": null,
			"endBinding": {
				"elementId": "2h6pZk9i",
				"focus": 0.3703673930161226,
				"gap": 8.639740801624214
			},
			"lastCommittedPoint": null,
			"startArrowhead": null,
			"endArrowhead": null,
			"points": [
				[
					0,
					0
				],
				[
					137.6065545581912,
					-10.068772284745705
				]
			]
		},
		{
			"type": "text",
			"version": 50,
			"versionNonce": 1327961675,
			"isDeleted": false,
			"id": "2h6pZk9i",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -225.84064024689786,
			"y": 130.04029751939285,
			"strokeColor": "#e03131",
			"backgroundColor": "transparent",
			"width": 55.578125,
			"height": 19.2,
			"seed": 2073676299,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "Uh4-_uKI8k-Yx4YiJzjK2",
					"type": "arrow"
				}
			],
			"updated": 1697726249341,
			"link": null,
			"locked": false,
			"fontSize": 16,
			"fontFamily": 4,
			"text": "入口函数",
			"rawText": "入口函数",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "入口函数",
			"lineHeight": 1.2,
			"baseline": 15
		},
		{
			"type": "line",
			"version": 165,
			"versionNonce": 1798604773,
			"isDeleted": false,
			"id": "Clf4_B745-_VwgxGgu96i",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -375.44319303496184,
			"y": -44.48508874953252,
			"strokeColor": "#e03131",
			"backgroundColor": "transparent",
			"width": 98.26314674293008,
			"height": 185.65500354340514,
			"seed": 1675773989,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1697726249341,
			"link": null,
			"locked": false,
			"startBinding": null,
			"endBinding": null,
			"lastCommittedPoint": null,
			"startArrowhead": null,
			"endArrowhead": null,
			"points": [
				[
					0,
					0
				],
				[
					-98.26314674293008,
					85.44491969249556
				],
				[
					-73.29716954867001,
					185.65500354340514
				]
			]
		},
		{
			"type": "image",
			"version": 160,
			"versionNonce": 1982076139,
			"isDeleted": false,
			"id": "uCh6ErE5Dji3CUZbf5EHF",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -331.6493542339414,
			"y": 221.13871342899677,
			"strokeColor": "transparent",
			"backgroundColor": "transparent",
			"width": 303.6446511001844,
			"height": 120.82526741694838,
			"seed": 1284879915,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697726249342,
			"link": null,
			"locked": false,
			"status": "pending",
			"fileId": "f790cb14c9e6cd814a6ef9b969b652b1cc719915",
			"scale": [
				1,
				1
			]
		},
		{
			"type": "rectangle",
			"version": 66,
			"versionNonce": 2105819973,
			"isDeleted": false,
			"id": "d1-YwMkJU-tZvrSuNnlqk",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -292.01622267564034,
			"y": 324.70322835780956,
			"strokeColor": "#e03131",
			"backgroundColor": "transparent",
			"width": 156.78516843389724,
			"height": 11.986633672316259,
			"seed": 1463524363,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 3
			},
			"boundElements": [],
			"updated": 1697726249342,
			"link": null,
			"locked": false
		},
		{
			"type": "line",
			"version": 51,
			"versionNonce": 1044922251,
			"isDeleted": false,
			"id": "aWlcRq4KVNvbHtmTNwCaa",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -379.4978148199068,
			"y": 209.65008218065282,
			"strokeColor": "#e03131",
			"backgroundColor": "transparent",
			"width": 49.43618716992296,
			"height": 39.8114427651592,
			"seed": 344099205,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1697726249342,
			"link": null,
			"locked": false,
			"startBinding": null,
			"endBinding": null,
			"lastCommittedPoint": null,
			"startArrowhead": null,
			"endArrowhead": null,
			"points": [
				[
					0,
					0
				],
				[
					49.43618716992296,
					39.8114427651592
				]
			]
		},
		{
			"type": "image",
			"version": 254,
			"versionNonce": 1493537445,
			"isDeleted": false,
			"id": "3P3Zv-pnOR_ImxQNs3cqX",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 85.9098713955087,
			"y": -102.51854632024245,
			"strokeColor": "transparent",
			"backgroundColor": "transparent",
			"width": 311.46680496762565,
			"height": 212.61935366887224,
			"seed": 740588011,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "SYM9phqbQ2LeTZiboh9RQ",
					"type": "arrow"
				}
			],
			"updated": 1697726249342,
			"link": null,
			"locked": false,
			"status": "pending",
			"fileId": "bd14cd015dd5ec368d2ef73e6845a6aa51b0158e",
			"scale": [
				1,
				1
			]
		},
		{
			"type": "rectangle",
			"version": 94,
			"versionNonce": 2129826533,
			"isDeleted": false,
			"id": "1JGsTIrSeAWW_pZEs7b9t",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -450.6016847284913,
			"y": 41.473267721838596,
			"strokeColor": "#e03131",
			"backgroundColor": "transparent",
			"width": 292.14552718019814,
			"height": 30.292769953658507,
			"seed": 345399621,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 3
			},
			"boundElements": [
				{
					"id": "nl768u3XZXjIFBwVbzzsk",
					"type": "arrow"
				}
			],
			"updated": 1697726249342,
			"link": null,
			"locked": false
		},
		{
			"type": "arrow",
			"version": 66,
			"versionNonce": 1461626469,
			"isDeleted": false,
			"id": "SYM9phqbQ2LeTZiboh9RQ",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -153.25266027567483,
			"y": -43.13577129425664,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 224.09872767171572,
			"height": 2.2240640361960047,
			"seed": 960352325,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1697726425425,
			"link": null,
			"locked": false,
			"startBinding": null,
			"endBinding": {
				"elementId": "3P3Zv-pnOR_ImxQNs3cqX",
				"focus": 0.3987544754707457,
				"gap": 15.063803999467837
			},
			"lastCommittedPoint": null,
			"startArrowhead": null,
			"endArrowhead": "triangle",
			"points": [
				[
					0,
					0
				],
				[
					224.09872767171572,
					2.2240640361960047
				]
			]
		},
		{
			"type": "text",
			"version": 184,
			"versionNonce": 1656930955,
			"isDeleted": false,
			"id": "vWh3q4oj",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 80.30310258659276,
			"y": 132.16481880089069,
			"strokeColor": "#2f9e44",
			"backgroundColor": "transparent",
			"width": 277.7734375,
			"height": 38.4,
			"seed": 2046021355,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697727882205,
			"link": null,
			"locked": false,
			"fontSize": 16,
			"fontFamily": 4,
			"text": "此时还是正常的elf文件，开头是elf头等一系列\n信息，然后是text节等",
			"rawText": "此时还是正常的elf文件，开头是elf头等一系列\n信息，然后是text节等",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "此时还是正常的elf文件，开头是elf头等一系列\n信息，然后是text节等",
			"lineHeight": 1.2,
			"baseline": 34
		},
		{
			"type": "text",
			"version": 255,
			"versionNonce": 2048305189,
			"isDeleted": false,
			"id": "LkCiuhJS",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 53.53721239629414,
			"y": 224.53338102623485,
			"strokeColor": "#e03131",
			"backgroundColor": "transparent",
			"width": 363.703125,
			"height": 38.4,
			"seed": 1411980683,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697726373452,
			"link": null,
			"locked": false,
			"fontSize": 16,
			"fontFamily": 4,
			"text": "但对于直接运行在裸机上的程序来说，我们并不需要elf头\n因此，我们通过 objcopy 命令去掉没有用的信息。 ",
			"rawText": "但对于直接运行在裸机上的程序来说，我们并不需要elf头\n因此，我们通过 objcopy 命令去掉没有用的信息。 ",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "但对于直接运行在裸机上的程序来说，我们并不需要elf头\n因此，我们通过 objcopy 命令去掉没有用的信息。 ",
			"lineHeight": 1.2,
			"baseline": 34
		},
		{
			"type": "arrow",
			"version": 355,
			"versionNonce": 219683083,
			"isDeleted": false,
			"id": "nl768u3XZXjIFBwVbzzsk",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -146.9548037603106,
			"y": 66.93526914651135,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 191.53890814788133,
			"height": 251.11423250469153,
			"seed": 745704517,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1697726427945,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "1JGsTIrSeAWW_pZEs7b9t",
				"focus": -0.950003093024031,
				"gap": 11.50135378798251
			},
			"endBinding": {
				"elementId": "I757gAa3M8H0zXaRCt2o7",
				"focus": -0.9116476149887971,
				"gap": 11.352579705239066
			},
			"lastCommittedPoint": null,
			"startArrowhead": null,
			"endArrowhead": "triangle",
			"points": [
				[
					0,
					0
				],
				[
					191.53890814788133,
					251.11423250469153
				]
			]
		},
		{
			"type": "image",
			"version": 216,
			"versionNonce": 1503194123,
			"isDeleted": false,
			"id": "I757gAa3M8H0zXaRCt2o7",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 55.9366840928098,
			"y": 308.4409913770201,
			"strokeColor": "transparent",
			"backgroundColor": "transparent",
			"width": 362.65668323234956,
			"height": 47.598689674245875,
			"seed": 1757266981,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "nl768u3XZXjIFBwVbzzsk",
					"type": "arrow"
				}
			],
			"updated": 1697726402924,
			"link": null,
			"locked": false,
			"status": "pending",
			"fileId": "2bfee2a4efdc726671452e5bdd9fdc4a77fd4e9f",
			"scale": [
				1,
				1
			]
		},
		{
			"type": "text",
			"version": 106,
			"versionNonce": 945477643,
			"isDeleted": false,
			"id": "APr21oqy",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 69.81086303034644,
			"y": 275.59954964832684,
			"strokeColor": "#2f9e44",
			"backgroundColor": "transparent",
			"width": 306.9140625,
			"height": 19.2,
			"seed": 807468613,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697726401526,
			"link": null,
			"locked": false,
			"fontSize": 16,
			"fontFamily": 4,
			"text": "此时二进制文件的text, data等也是从 0x0 开始",
			"rawText": "此时二进制文件的text, data等也是从 0x0 开始",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "此时二进制文件的text, data等也是从 0x0 开始",
			"lineHeight": 1.2,
			"baseline": 15
		},
		{
			"type": "arrow",
			"version": 481,
			"versionNonce": 1096349003,
			"isDeleted": false,
			"id": "nufiIflRemoFl5Pk9VGUI",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -163.0353630939121,
			"y": 99.17197862087616,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 206.1000272304216,
			"height": 340.074159257344,
			"seed": 1227687211,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1697727830447,
			"link": null,
			"locked": false,
			"startBinding": null,
			"endBinding": {
				"elementId": "sLPU6rsu",
				"focus": -0.8769071655256475,
				"gap": 13.669920182469127
			},
			"lastCommittedPoint": null,
			"startArrowhead": null,
			"endArrowhead": "triangle",
			"points": [
				[
					0,
					0
				],
				[
					137.7694579509283,
					175.68122519045866
				],
				[
					206.1000272304216,
					340.074159257344
				]
			]
		},
		{
			"type": "text",
			"version": 404,
			"versionNonce": 660314699,
			"isDeleted": false,
			"id": "sLPU6rsu",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 51.91798893553539,
			"y": 452.91605806068924,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 399.3828125,
			"height": 76.8,
			"seed": 1319243115,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "nufiIflRemoFl5Pk9VGUI",
					"type": "arrow"
				}
			],
			"updated": 1697726626333,
			"link": null,
			"locked": false,
			"fontSize": 16,
			"fontFamily": 4,
			"text": "这个命令是把我们的 xx.bin 文件加载到 nemu 中执行，在\nNEMU中，我们通过load_img函数把 xx.bin 加载进来，并放到\n合适的位置（IMAGE_START)处，因为 xx.bin 中的位置信息都是\n基于 IMAGE_START 的，这也是am的脚本所规定的。",
			"rawText": "这个命令是把我们的 xx.bin 文件加载到 nemu 中执行，在\nNEMU中，我们通过load_img函数把 xx.bin 加载进来，并放到\n合适的位置（IMAGE_START)处，因为 xx.bin 中的位置信息都是\n基于 IMAGE_START 的，这也是am的脚本所规定的。",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "这个命令是把我们的 xx.bin 文件加载到 nemu 中执行，在\nNEMU中，我们通过load_img函数把 xx.bin 加载进来，并放到\n合适的位置（IMAGE_START)处，因为 xx.bin 中的位置信息都是\n基于 IMAGE_START 的，这也是am的脚本所规定的。",
			"lineHeight": 1.2,
			"baseline": 72
		},
		{
			"type": "image",
			"version": 103,
			"versionNonce": 449930117,
			"isDeleted": false,
			"id": "NDrgUfbL83eoMeEzT-68u",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 50.35084476223014,
			"y": 541.4625126839883,
			"strokeColor": "transparent",
			"backgroundColor": "transparent",
			"width": 416.3909182032018,
			"height": 260.53348423686447,
			"seed": 1098491179,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "nufiIflRemoFl5Pk9VGUI",
					"type": "arrow"
				}
			],
			"updated": 1697727821199,
			"link": null,
			"locked": false,
			"status": "pending",
			"fileId": "b1d65c508c598b46a7268de97530be25e17a74ca",
			"scale": [
				1,
				1
			]
		},
		{
			"type": "text",
			"version": 237,
			"versionNonce": 1391223691,
			"isDeleted": false,
			"id": "KTapuQSl",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 57.51738084155906,
			"y": 832.0163160921782,
			"strokeColor": "#2f9e44",
			"backgroundColor": "transparent",
			"width": 398.484375,
			"height": 96,
			"seed": 1896045029,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697726714125,
			"link": null,
			"locked": false,
			"fontSize": 16,
			"fontFamily": 4,
			"text": "然后让nemu的cpu.pc 指向IMAGE_START 的初始位置，就开始\n状态机的执行过程：\n取指\n译码\n执行",
			"rawText": "然后让nemu的cpu.pc 指向IMAGE_START 的初始位置，就开始\n状态机的执行过程：\n取指\n译码\n执行",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "然后让nemu的cpu.pc 指向IMAGE_START 的初始位置，就开始\n状态机的执行过程：\n取指\n译码\n执行",
			"lineHeight": 1.2,
			"baseline": 91
		},
		{
			"type": "text",
			"version": 171,
			"versionNonce": 1060445413,
			"isDeleted": false,
			"id": "JgM1m01e",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 878.9938117731285,
			"y": -235.0919190138302,
			"strokeColor": "#1971c2",
			"backgroundColor": "transparent",
			"width": 455.3555908203125,
			"height": 44.8527444943452,
			"seed": 731850885,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697726757047,
			"link": null,
			"locked": false,
			"fontSize": 37.377287078621,
			"fontFamily": 4,
			"text": "操作系统的用户程序执行过程",
			"rawText": "操作系统的用户程序执行过程",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "操作系统的用户程序执行过程",
			"lineHeight": 1.2,
			"baseline": 34
		},
		{
			"type": "text",
			"version": 275,
			"versionNonce": 1389941739,
			"isDeleted": false,
			"id": "AdXohi2z",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 637.7223597333754,
			"y": -129.67722939341,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 359.46875,
			"height": 38.4,
			"seed": 2072213067,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697727052587,
			"link": null,
			"locked": false,
			"fontSize": 16,
			"fontFamily": 4,
			"text": "众所周知，操作系统也是一个程序，也是通过硬件执行的。\n但它特殊在什么地方呢？",
			"rawText": "众所周知，操作系统也是一个程序，也是通过硬件执行的。\n但它特殊在什么地方呢？",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "众所周知，操作系统也是一个程序，也是通过硬件执行的。\n但它特殊在什么地方呢？",
			"lineHeight": 1.2,
			"baseline": 34
		},
		{
			"type": "text",
			"version": 100,
			"versionNonce": 727101163,
			"isDeleted": false,
			"id": "t58LRyv3",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 639.4351195012225,
			"y": -77.7672908715218,
			"strokeColor": "#e03131",
			"backgroundColor": "transparent",
			"width": 298.1875,
			"height": 19.2,
			"seed": 1812374021,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697727029184,
			"link": null,
			"locked": false,
			"fontSize": 16,
			"fontFamily": 4,
			"text": "OS最重要的特点就是可以管理其他程序的执行",
			"rawText": "OS最重要的特点就是可以管理其他程序的执行",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "OS最重要的特点就是可以管理其他程序的执行",
			"lineHeight": 1.2,
			"baseline": 15
		},
		{
			"type": "text",
			"version": 302,
			"versionNonce": 1997997541,
			"isDeleted": false,
			"id": "1Rh4kt74",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 636.8087363566159,
			"y": -42.12676187755369,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 370.53125,
			"height": 57.599999999999994,
			"seed": 774848101,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697727110509,
			"link": null,
			"locked": false,
			"fontSize": 16,
			"fontFamily": 4,
			"text": "有了操作系统后，我们就可以实现一个永不停止的计算机了。\n当一个程序运行完毕后，操作系统会自动加载另一个程序，\n周而复始。",
			"rawText": "有了操作系统后，我们就可以实现一个永不停止的计算机了。\n当一个程序运行完毕后，操作系统会自动加载另一个程序，\n周而复始。",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "有了操作系统后，我们就可以实现一个永不停止的计算机了。\n当一个程序运行完毕后，操作系统会自动加载另一个程序，\n周而复始。",
			"lineHeight": 1.2,
			"baseline": 53
		},
		{
			"type": "rectangle",
			"version": 78,
			"versionNonce": 2096941285,
			"isDeleted": false,
			"id": "jopksXZeZs-uGPVxmDfX_",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -325.1913877265137,
			"y": 278.9841004088498,
			"strokeColor": "#e03131",
			"backgroundColor": "transparent",
			"width": 291.9820894152933,
			"height": 14.065582380470914,
			"seed": 338889387,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 3
			},
			"boundElements": [
				{
					"id": "wgJl35831m6PBqlsttskp",
					"type": "arrow"
				}
			],
			"updated": 1697727872001,
			"link": null,
			"locked": false
		},
		{
			"type": "image",
			"version": 74,
			"versionNonce": 879858597,
			"isDeleted": false,
			"id": "afs3OV0XWDTO2NC8GV3O5",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -469.218215909361,
			"y": 550.9113577272236,
			"strokeColor": "transparent",
			"backgroundColor": "transparent",
			"width": 441.85021298081466,
			"height": 228.59611713243538,
			"seed": 1521804197,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "wgJl35831m6PBqlsttskp",
					"type": "arrow"
				}
			],
			"updated": 1697727872001,
			"link": null,
			"locked": false,
			"status": "pending",
			"fileId": "31d8ae4ca8924eaf3ce1d066bfa5c6985aee224a",
			"scale": [
				1,
				1
			]
		},
		{
			"type": "arrow",
			"version": 50,
			"versionNonce": 245130309,
			"isDeleted": false,
			"id": "wgJl35831m6PBqlsttskp",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -85.46713451012897,
			"y": 298.4097642933574,
			"strokeColor": "#e03131",
			"backgroundColor": "transparent",
			"width": 114.2980585662176,
			"height": 246.52522435850847,
			"seed": 1735501643,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1697727872001,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "jopksXZeZs-uGPVxmDfX_",
				"focus": -0.6665183265084873,
				"gap": 5.360081504036657
			},
			"endBinding": {
				"elementId": "afs3OV0XWDTO2NC8GV3O5",
				"focus": -0.026415518811546704,
				"gap": 5.976369075357809
			},
			"lastCommittedPoint": null,
			"startArrowhead": null,
			"endArrowhead": "triangle",
			"points": [
				[
					0,
					0
				],
				[
					-114.2980585662176,
					246.52522435850847
				]
			]
		},
		{
			"type": "text",
			"version": 322,
			"versionNonce": 1713227813,
			"isDeleted": false,
			"id": "RpnA5CSZ",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -459.73724785441016,
			"y": 796.6895359513127,
			"strokeColor": "#e03131",
			"backgroundColor": "transparent",
			"width": 344.59454345703125,
			"height": 60.34630571563544,
			"seed": 731785835,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697727958218,
			"link": null,
			"locked": false,
			"fontSize": 16.76286269878762,
			"fontFamily": 4,
			"text": "可以看到，0x1000以内的是elf头，然后align=0x1000，从\n0x2000开始就是text节了，但elf头中记录了virtual的虚拟\n地址（也就是程序执行过程中所使用的地址）。",
			"rawText": "可以看到，0x1000以内的是elf头，然后align=0x1000，从\n0x2000开始就是text节了，但elf头中记录了virtual的虚拟\n地址（也就是程序执行过程中所使用的地址）。",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "可以看到，0x1000以内的是elf头，然后align=0x1000，从\n0x2000开始就是text节了，但elf头中记录了virtual的虚拟\n地址（也就是程序执行过程中所使用的地址）。",
			"lineHeight": 1.2,
			"baseline": 55
		},
		{
			"type": "text",
			"version": 133,
			"versionNonce": 1039123147,
			"isDeleted": false,
			"id": "rE1wNLdi",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -457.19701970924996,
			"y": 887.1122745496889,
			"strokeColor": "#9c36b5",
			"backgroundColor": "transparent",
			"width": 383.296875,
			"height": 19.2,
			"seed": 115544325,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697728091095,
			"link": null,
			"locked": false,
			"fontSize": 16,
			"fontFamily": 4,
			"text": "具体可以看CSAPP链接那一章，还有相对地址寻址的一些问题",
			"rawText": "具体可以看CSAPP链接那一章，还有相对地址寻址的一些问题",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "具体可以看CSAPP链接那一章，还有相对地址寻址的一些问题",
			"lineHeight": 1.2,
			"baseline": 15
		}
	],
	"appState": {
		"theme": "light",
		"viewBackgroundColor": "#ffffff",
		"currentItemStrokeColor": "#9c36b5",
		"currentItemBackgroundColor": "transparent",
		"currentItemFillStyle": "hachure",
		"currentItemStrokeWidth": 1,
		"currentItemStrokeStyle": "solid",
		"currentItemRoughness": 1,
		"currentItemOpacity": 100,
		"currentItemFontFamily": 3,
		"currentItemFontSize": 16,
		"currentItemTextAlign": "left",
		"currentItemStartArrowhead": null,
		"currentItemEndArrowhead": "triangle",
		"scrollX": 511.6304550666986,
		"scrollY": -117.0340326674339,
		"zoom": {
			"value": 2.4400723223589535
		},
		"currentItemRoundness": "round",
		"gridSize": null,
		"gridColor": {
			"Bold": "#C9C9C9FF",
			"Regular": "#EDEDEDFF"
		},
		"currentStrokeOptions": null,
		"previousGridSize": null,
		"frameRendering": {
			"enabled": true,
			"clip": true,
			"name": true,
			"outline": true
		}
	},
	"files": {}
}
```
%%