---

excalidraw-plugin: parsed
tags: [excalidraw]

---
==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠==


# Text Elements
am-kernel/test/cpu-test/Makefile ^MxPuMJsJ

am-kernel/test/cpu-test/Makefile.dummy ^LR22KUy3

abstract-machine/Makefile ^c58E6EFG

abstract-machine/scripts/platform/nemu.mk ^Z0gpk2Ha

image ^z5Jf7YQn

run ^GC4YQmw8

gdb ^qXQ8U9Tm

## 5. Compilation Rules

### Rule (compile): a single `.c` -> `.o` (gcc)
$(DST_DIR)/%.o: %.c
        @mkdir -p $(dir $@) && echo + CC $<
        @$(CC) -std=gnu11 $(CFLAGS) -c -o $@ $(realpath $<)

### Rule (compile): a single `.cc` -> `.o` (g++)
$(DST_DIR)/%.o: %.cc
        @mkdir -p $(dir $@) && echo + CXX $<
        @$(CXX) -std=c++17 $(CXXFLAGS) -c -o $@ $(realpath $<)

### Rule (compile): a single `.cpp` -> `.o` (g++)
$(DST_DIR)/%.o: %.cpp
        @mkdir -p $(dir $@) && echo + CXX $<
        @$(CXX) -std=c++17 $(CXXFLAGS) -c -o $@ $(realpath $<)

### Rule (compile): a single `.S` -> `.o` (gcc, which calls as)
$(DST_DIR)/%.o: %.S
        @mkdir -p $(dir $@) && echo + AS $<
        @$(AS) $(ASFLAGS) -c -o $@ $(realpath $<)

### Rule (recursive make): build a dependent library (am, klib, ...)
$(LIBS): %:
        @$(MAKE) -s -C $(AM_HOME)/$* archive

### Rule (link): objects (`*.o`) and libraries (`*.a`) -> `IMAGE.elf`, 
    the final ELF binary to be packed into image (ld)
$(IMAGE).elf: $(OBJS) am $(LIBS)
        @echo + LD "->" $(IMAGE_REL).elf
        @$(LD) $(LDFLAGS) -o $(IMAGE).elf $(LINKAGE)

### Rule (archive): objects (`*.o`) -> `ARCHIVE.a` (ar)
$(ARCHIVE): $(OBJS)
        @echo + AR "->" $(shell realpath $@ --relative-to .)
        @ar rcs $(ARCHIVE) $(OBJS)
### Build order control
image: image-dep
archive: $(ARCHIVE)
image-dep: $(OBJS) am $(LIBS)
        @echo \# Creating image [$(ARCH)]
        @echo $(NAME)
.PHONY: image image-dep archive run $(LIBS)

### Clean a single project (remove `build/`)
clean:
        rm -rf Makefile.html $(WORK_DIR)/build/
.PHONY: clean

### Clean all sub-projects within depth 2 (and ignore errors)
CLEAN_ALL = $(dir $(shell find . -mindepth 2 -name Makefile))
clean-all: $(CLEAN_ALL) clean
$(CLEAN_ALL):
        -@$(MAKE) -s -C $@ clean
.PHONY: clean-all $(CLEAN_ALL)
 ^TTNv9hL7

image  ^WUGoJDkm

make -s -C $(AM_HOME)/am archive ^zYhuKyeF

make -s -C $(AM_HOME)/klib archive ^6bBIeX5W

image: $(IMAGE).elf
        @$(OBJDUMP) -d $(IMAGE).elf > $(IMAGE).txt
        @echo + OBJCOPY "->" $(IMAGE_REL).bin
        @$(OBJCOPY) -S --set-section-flags .bss=alloc,contents -O binary $(IMAGE).elf $(IMAGE).bin

run: image
        $(MAKE) -C $(NEMU_HOME) ISA=$(ISA) run ARGS="$(NEMUFLAGS)"

gdb: image
        $(MAKE) -C $(NEMU_HOME) ISA=$(ISA) gdb ARGS="$(NEMUFLAGS)" ^SmddMurL

image-dep ^YRDS7gjI

$(OBJS) ^BdLhhQo0

am ^y7m6YyCv

$(LIBS) ^UVLCQG5Q

$(IMAGE).elf ^e6xqDdQu

$(OBJS) ^hTpkA5Gx

am ^DenlaT2q

$(LIBS) ^cOh8lggy

主要是输出相关信息 ^TeMYjIe3

执行链接操作 ^41RWyTm3

make image ^2Wm9oysd

archive ^td6n4hRq

make archive ^ZqwgvBri

$(ARCHIVE) ^G9wtN7WM

$(OBJS) ^c0yuOLfO

ar rcs $(ARCHIVE) $(OBJS) ^WpVpxfNp

OBJS      = $(addprefix $(DST_DIR)/, $(addsuffix .o, $(basename $(SRCS)))) ^KImVYLci

SRCS      = $(addprefix src/, $(AM_SRCS)) ^0rHVoPdR

AM_SRCS := native/trm.c \
           native/ioe.c \
           native/cte.c \
           native/trap.S \
           native/vme.c \
           native/mpe.c \
           native/platform.c \
           native/native-input.c \
           native/native-timer.c \
           native/native-gpu.c \
           native/native-audio.c \
 ^FmKgTyuM

在native.mk中 ^FsFOITw4

在am/下的makefile中 ^gnPS2zPk

通过这个规则调用 ^YsuoZVAX


# Embedded files
524147e6d4c41610c10cb1f08397fa795ef3ccbd: [[Pasted Image 20230624121753_914.png]]
f5a389f897a0f6b3fdbf6a3511210fc6c45c20d4: [[Pasted Image 20230624121823_932.png]]

%%
# Drawing
```json
{
	"type": "excalidraw",
	"version": 2,
	"source": "https://github.com/zsviczian/obsidian-excalidraw-plugin/releases/tag/2.0.17",
	"elements": [
		{
			"type": "rectangle",
			"version": 90,
			"versionNonce": 1990777605,
			"isDeleted": false,
			"id": "NhOay6-CgUQqDWQ6QUeSs",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 140.59731593013396,
			"y": 838.330850957034,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 1186.6317258849995,
			"height": 127.52508529547345,
			"seed": 279973352,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 3
			},
			"boundElements": [
				{
					"id": "4Q2AUADTzsUSSgnyv2onA",
					"type": "arrow"
				}
			],
			"updated": 1689210237559,
			"link": null,
			"locked": false
		},
		{
			"type": "text",
			"version": 648,
			"versionNonce": 1629559391,
			"isDeleted": false,
			"id": "TTNv9hL7",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 2578.425335646348,
			"y": -1057.5889405751843,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 900.673828125,
			"height": 1455.2653295501013,
			"seed": 1245179368,
			"groupIds": [
				"Zj5eowInT-v7-pWnUoVmA"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "4Q2AUADTzsUSSgnyv2onA",
					"type": "arrow"
				}
			],
			"updated": 1705733612756,
			"link": null,
			"locked": false,
			"fontSize": 21.65573407068603,
			"fontFamily": 3,
			"text": "## 5. Compilation Rules\n\n### Rule (compile): a single `.c` -> `.o` (gcc)\n$(DST_DIR)/%.o: %.c\n        @mkdir -p $(dir $@) && echo + CC $<\n        @$(CC) -std=gnu11 $(CFLAGS) -c -o $@ $(realpath $<)\n\n### Rule (compile): a single `.cc` -> `.o` (g++)\n$(DST_DIR)/%.o: %.cc\n        @mkdir -p $(dir $@) && echo + CXX $<\n        @$(CXX) -std=c++17 $(CXXFLAGS) -c -o $@ $(realpath $<)\n\n### Rule (compile): a single `.cpp` -> `.o` (g++)\n$(DST_DIR)/%.o: %.cpp\n        @mkdir -p $(dir $@) && echo + CXX $<\n        @$(CXX) -std=c++17 $(CXXFLAGS) -c -o $@ $(realpath $<)\n\n### Rule (compile): a single `.S` -> `.o` (gcc, which calls as)\n$(DST_DIR)/%.o: %.S\n        @mkdir -p $(dir $@) && echo + AS $<\n        @$(AS) $(ASFLAGS) -c -o $@ $(realpath $<)\n\n### Rule (recursive make): build a dependent library (am, klib, ...)\n$(LIBS): %:\n        @$(MAKE) -s -C $(AM_HOME)/$* archive\n\n### Rule (link): objects (`*.o`) and libraries (`*.a`) -> `IMAGE.elf`, \n    the final ELF binary to be packed into image (ld)\n$(IMAGE).elf: $(OBJS) am $(LIBS)\n        @echo + LD \"->\" $(IMAGE_REL).elf\n        @$(LD) $(LDFLAGS) -o $(IMAGE).elf $(LINKAGE)\n\n### Rule (archive): objects (`*.o`) -> `ARCHIVE.a` (ar)\n$(ARCHIVE): $(OBJS)\n        @echo + AR \"->\" $(shell realpath $@ --relative-to .)\n        @ar rcs $(ARCHIVE) $(OBJS)\n### Build order control\nimage: image-dep\narchive: $(ARCHIVE)\nimage-dep: $(OBJS) am $(LIBS)\n        @echo \\# Creating image [$(ARCH)]\n        @echo $(NAME)\n.PHONY: image image-dep archive run $(LIBS)\n\n### Clean a single project (remove `build/`)\nclean:\n        rm -rf Makefile.html $(WORK_DIR)/build/\n.PHONY: clean\n\n### Clean all sub-projects within depth 2 (and ignore errors)\nCLEAN_ALL = $(dir $(shell find . -mindepth 2 -name Makefile))\nclean-all: $(CLEAN_ALL) clean\n$(CLEAN_ALL):\n        -@$(MAKE) -s -C $@ clean\n.PHONY: clean-all $(CLEAN_ALL)\n",
			"rawText": "## 5. Compilation Rules\n\n### Rule (compile): a single `.c` -> `.o` (gcc)\n$(DST_DIR)/%.o: %.c\n        @mkdir -p $(dir $@) && echo + CC $<\n        @$(CC) -std=gnu11 $(CFLAGS) -c -o $@ $(realpath $<)\n\n### Rule (compile): a single `.cc` -> `.o` (g++)\n$(DST_DIR)/%.o: %.cc\n        @mkdir -p $(dir $@) && echo + CXX $<\n        @$(CXX) -std=c++17 $(CXXFLAGS) -c -o $@ $(realpath $<)\n\n### Rule (compile): a single `.cpp` -> `.o` (g++)\n$(DST_DIR)/%.o: %.cpp\n        @mkdir -p $(dir $@) && echo + CXX $<\n        @$(CXX) -std=c++17 $(CXXFLAGS) -c -o $@ $(realpath $<)\n\n### Rule (compile): a single `.S` -> `.o` (gcc, which calls as)\n$(DST_DIR)/%.o: %.S\n        @mkdir -p $(dir $@) && echo + AS $<\n        @$(AS) $(ASFLAGS) -c -o $@ $(realpath $<)\n\n### Rule (recursive make): build a dependent library (am, klib, ...)\n$(LIBS): %:\n        @$(MAKE) -s -C $(AM_HOME)/$* archive\n\n### Rule (link): objects (`*.o`) and libraries (`*.a`) -> `IMAGE.elf`, \n    the final ELF binary to be packed into image (ld)\n$(IMAGE).elf: $(OBJS) am $(LIBS)\n        @echo + LD \"->\" $(IMAGE_REL).elf\n        @$(LD) $(LDFLAGS) -o $(IMAGE).elf $(LINKAGE)\n\n### Rule (archive): objects (`*.o`) -> `ARCHIVE.a` (ar)\n$(ARCHIVE): $(OBJS)\n        @echo + AR \"->\" $(shell realpath $@ --relative-to .)\n        @ar rcs $(ARCHIVE) $(OBJS)\n### Build order control\nimage: image-dep\narchive: $(ARCHIVE)\nimage-dep: $(OBJS) am $(LIBS)\n        @echo \\# Creating image [$(ARCH)]\n        @echo $(NAME)\n.PHONY: image image-dep archive run $(LIBS)\n\n### Clean a single project (remove `build/`)\nclean:\n        rm -rf Makefile.html $(WORK_DIR)/build/\n.PHONY: clean\n\n### Clean all sub-projects within depth 2 (and ignore errors)\nCLEAN_ALL = $(dir $(shell find . -mindepth 2 -name Makefile))\nclean-all: $(CLEAN_ALL) clean\n$(CLEAN_ALL):\n        -@$(MAKE) -s -C $@ clean\n.PHONY: clean-all $(CLEAN_ALL)\n",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "## 5. Compilation Rules\n\n### Rule (compile): a single `.c` -> `.o` (gcc)\n$(DST_DIR)/%.o: %.c\n        @mkdir -p $(dir $@) && echo + CC $<\n        @$(CC) -std=gnu11 $(CFLAGS) -c -o $@ $(realpath $<)\n\n### Rule (compile): a single `.cc` -> `.o` (g++)\n$(DST_DIR)/%.o: %.cc\n        @mkdir -p $(dir $@) && echo + CXX $<\n        @$(CXX) -std=c++17 $(CXXFLAGS) -c -o $@ $(realpath $<)\n\n### Rule (compile): a single `.cpp` -> `.o` (g++)\n$(DST_DIR)/%.o: %.cpp\n        @mkdir -p $(dir $@) && echo + CXX $<\n        @$(CXX) -std=c++17 $(CXXFLAGS) -c -o $@ $(realpath $<)\n\n### Rule (compile): a single `.S` -> `.o` (gcc, which calls as)\n$(DST_DIR)/%.o: %.S\n        @mkdir -p $(dir $@) && echo + AS $<\n        @$(AS) $(ASFLAGS) -c -o $@ $(realpath $<)\n\n### Rule (recursive make): build a dependent library (am, klib, ...)\n$(LIBS): %:\n        @$(MAKE) -s -C $(AM_HOME)/$* archive\n\n### Rule (link): objects (`*.o`) and libraries (`*.a`) -> `IMAGE.elf`, \n    the final ELF binary to be packed into image (ld)\n$(IMAGE).elf: $(OBJS) am $(LIBS)\n        @echo + LD \"->\" $(IMAGE_REL).elf\n        @$(LD) $(LDFLAGS) -o $(IMAGE).elf $(LINKAGE)\n\n### Rule (archive): objects (`*.o`) -> `ARCHIVE.a` (ar)\n$(ARCHIVE): $(OBJS)\n        @echo + AR \"->\" $(shell realpath $@ --relative-to .)\n        @ar rcs $(ARCHIVE) $(OBJS)\n### Build order control\nimage: image-dep\narchive: $(ARCHIVE)\nimage-dep: $(OBJS) am $(LIBS)\n        @echo \\# Creating image [$(ARCH)]\n        @echo $(NAME)\n.PHONY: image image-dep archive run $(LIBS)\n\n### Clean a single project (remove `build/`)\nclean:\n        rm -rf Makefile.html $(WORK_DIR)/build/\n.PHONY: clean\n\n### Clean all sub-projects within depth 2 (and ignore errors)\nCLEAN_ALL = $(dir $(shell find . -mindepth 2 -name Makefile))\nclean-all: $(CLEAN_ALL) clean\n$(CLEAN_ALL):\n        -@$(MAKE) -s -C $@ clean\n.PHONY: clean-all $(CLEAN_ALL)\n",
			"lineHeight": 1.2,
			"baseline": 1450
		},
		{
			"type": "rectangle",
			"version": 289,
			"versionNonce": 960574053,
			"isDeleted": false,
			"id": "haF_o66cQEtclYmBg1zsi",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 2564.290050581392,
			"y": -92.94126175269668,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 233.99882185582192,
			"height": 25.267478416356425,
			"seed": 970831080,
			"groupIds": [
				"Zj5eowInT-v7-pWnUoVmA"
			],
			"frameId": null,
			"roundness": {
				"type": 3
			},
			"boundElements": [
				{
					"id": "4Q2AUADTzsUSSgnyv2onA",
					"type": "arrow"
				}
			],
			"updated": 1689210237559,
			"link": null,
			"locked": false
		},
		{
			"type": "text",
			"version": 182,
			"versionNonce": 282820369,
			"isDeleted": false,
			"id": "MxPuMJsJ",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -144.59116570406354,
			"y": -751.5102793192013,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 375,
			"height": 24,
			"seed": 827936232,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "A_HxVS4cHGBWp61VxbGtH",
					"type": "arrow"
				},
				{
					"id": "JIQxtcanjm0eqLOaZnIA7",
					"type": "arrow"
				}
			],
			"updated": 1705733612757,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 3,
			"text": "am-kernel/test/cpu-test/Makefile",
			"rawText": "am-kernel/test/cpu-test/Makefile",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "am-kernel/test/cpu-test/Makefile",
			"lineHeight": 1.2,
			"baseline": 19
		},
		{
			"type": "arrow",
			"version": 433,
			"versionNonce": 1771544005,
			"isDeleted": false,
			"id": "A_HxVS4cHGBWp61VxbGtH",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 32.21280756598057,
			"y": -723.5102793192013,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 17.579843921967022,
			"height": 226.3370235248056,
			"seed": 2106751720,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237559,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "MxPuMJsJ",
				"focus": 0.050168159246875656,
				"gap": 4
			},
			"endBinding": {
				"elementId": "LR22KUy3",
				"focus": -0.04277083333333333,
				"gap": 9.000000000000057
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
					-17.579843921967022,
					226.3370235248056
				]
			]
		},
		{
			"type": "text",
			"version": 252,
			"versionNonce": 468481663,
			"isDeleted": false,
			"id": "LR22KUy3",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -200.09132125374583,
			"y": -488.1732557943957,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 445.3125,
			"height": 24,
			"seed": 1110798824,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "A_HxVS4cHGBWp61VxbGtH",
					"type": "arrow"
				},
				{
					"id": "1K5ncyoWPQQNTWm_LuRak",
					"type": "arrow"
				},
				{
					"id": "FFSnf4-_elMO4jOryGlTu",
					"type": "arrow"
				}
			],
			"updated": 1705733612757,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 3,
			"text": "am-kernel/test/cpu-test/Makefile.dummy",
			"rawText": "am-kernel/test/cpu-test/Makefile.dummy",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "am-kernel/test/cpu-test/Makefile.dummy",
			"lineHeight": 1.2,
			"baseline": 19
		},
		{
			"type": "image",
			"version": 268,
			"versionNonce": 1321835813,
			"isDeleted": false,
			"id": "cQAaURT7VmapGytccjwCQ",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 361.56355633691265,
			"y": -838.3120707930208,
			"strokeColor": "transparent",
			"backgroundColor": "transparent",
			"width": 763.0892263401748,
			"height": 130.36107616644654,
			"seed": 241158552,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "JIQxtcanjm0eqLOaZnIA7",
					"type": "arrow"
				}
			],
			"updated": 1689210237559,
			"link": null,
			"locked": false,
			"status": "pending",
			"fileId": "524147e6d4c41610c10cb1f08397fa795ef3ccbd",
			"scale": [
				1,
				1
			]
		},
		{
			"type": "arrow",
			"version": 434,
			"versionNonce": 302379947,
			"isDeleted": false,
			"id": "JIQxtcanjm0eqLOaZnIA7",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 244.94270837318743,
			"y": -735.3814581714475,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 104.0056990047176,
			"height": 66.62816029548662,
			"seed": 322606488,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237559,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "MxPuMJsJ",
				"gap": 14.533874077250942,
				"focus": 1.008743152813769
			},
			"endBinding": {
				"elementId": "cQAaURT7VmapGytccjwCQ",
				"gap": 12.615148959007533,
				"focus": 0.9088488134180599
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
					104.0056990047176,
					-66.62816029548662
				]
			]
		},
		{
			"type": "image",
			"version": 291,
			"versionNonce": 1883549829,
			"isDeleted": false,
			"id": "17XDGIts_CqzuyFDgmwbE",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 366.07892700699176,
			"y": -540.4373711677731,
			"strokeColor": "transparent",
			"backgroundColor": "transparent",
			"width": 802.150951687013,
			"height": 107.51050949693995,
			"seed": 1472025752,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "1K5ncyoWPQQNTWm_LuRak",
					"type": "arrow"
				}
			],
			"updated": 1689210237559,
			"link": null,
			"locked": false,
			"status": "pending",
			"fileId": "f5a389f897a0f6b3fdbf6a3511210fc6c45c20d4",
			"scale": [
				1,
				1
			]
		},
		{
			"type": "arrow",
			"version": 429,
			"versionNonce": 671106635,
			"isDeleted": false,
			"id": "1K5ncyoWPQQNTWm_LuRak",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 263.50806520055846,
			"y": -474.5588628404167,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 90.31450128463183,
			"height": 6.991885548723019,
			"seed": 1435386264,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237559,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "LR22KUy3",
				"gap": 18.286886454304273,
				"focus": 0.677469955164916
			},
			"endBinding": {
				"elementId": "17XDGIts_CqzuyFDgmwbE",
				"gap": 12.25636052180146,
				"focus": 0.3168146657027404
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
					90.31450128463183,
					-6.991885548723019
				]
			]
		},
		{
			"type": "arrow",
			"version": 626,
			"versionNonce": 2069335089,
			"isDeleted": false,
			"id": "FFSnf4-_elMO4jOryGlTu",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 16.92083754821076,
			"y": -455.38157567645544,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 22.98379619318883,
			"height": 712.0792084204279,
			"seed": 1810614248,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1705802076341,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "LR22KUy3",
				"gap": 8.791680117940246,
				"focus": 0.022296081383722896
			},
			"endBinding": {
				"elementId": "QbgoU5ygTXgCEN9ImVcWy",
				"gap": 8.374316713749174,
				"focus": -0.03857752277951054
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
					-22.98379619318883,
					712.0792084204279
				]
			]
		},
		{
			"type": "rectangle",
			"version": 32,
			"versionNonce": 1012352235,
			"isDeleted": false,
			"id": "QbgoU5ygTXgCEN9ImVcWy",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -209.3953888991329,
			"y": 265.07194945772164,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 421,
			"height": 44,
			"seed": 1350825112,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 3
			},
			"boundElements": [
				{
					"id": "FFSnf4-_elMO4jOryGlTu",
					"type": "arrow"
				},
				{
					"id": "y6OckG3skNOCpe7iyKDyt",
					"type": "arrow"
				},
				{
					"id": "c58E6EFG",
					"type": "text"
				},
				{
					"id": "55IkphsiQ9DvoClBu8K1h",
					"type": "arrow"
				},
				{
					"id": "JrzY3ZCS3Tg4bBdw7vw1i",
					"type": "arrow"
				}
			],
			"updated": 1689210237560,
			"link": null,
			"locked": false
		},
		{
			"type": "text",
			"version": 434,
			"versionNonce": 1341501023,
			"isDeleted": false,
			"id": "c58E6EFG",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -203.9735138991329,
			"y": 270.27194945772163,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 410.15625,
			"height": 33.6,
			"seed": 681895400,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1705796958684,
			"link": null,
			"locked": false,
			"fontSize": 28,
			"fontFamily": 3,
			"text": "abstract-machine/Makefile",
			"rawText": "abstract-machine/Makefile",
			"textAlign": "center",
			"verticalAlign": "middle",
			"containerId": "QbgoU5ygTXgCEN9ImVcWy",
			"originalText": "abstract-machine/Makefile",
			"lineHeight": 1.2,
			"baseline": 27
		},
		{
			"type": "arrow",
			"version": 438,
			"versionNonce": 1544877041,
			"isDeleted": false,
			"id": "y6OckG3skNOCpe7iyKDyt",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -5.332518100561306,
			"y": 318.4974794429266,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 7.025644086603865,
			"height": 887.084727446739,
			"seed": 1940988824,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1705802076342,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "QbgoU5ygTXgCEN9ImVcWy",
				"gap": 9.425529985204946,
				"focus": 0.0317362819473991
			},
			"endBinding": {
				"elementId": "Z0gpk2Ha",
				"gap": 9.98621044356696,
				"focus": 0.03278319948772638
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
					7.025644086603865,
					887.084727446739
				]
			]
		},
		{
			"type": "text",
			"version": 533,
			"versionNonce": 1075541233,
			"isDeleted": false,
			"id": "Z0gpk2Ha",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -246.24588701172547,
			"y": 1215.5684173332324,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 480.46875,
			"height": 24,
			"seed": 462149016,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "y6OckG3skNOCpe7iyKDyt",
					"type": "arrow"
				},
				{
					"id": "51K6BNeAV8qDbDjS5glGo",
					"type": "arrow"
				},
				{
					"id": "R2MYEktX2OEGynAmk2hDl",
					"type": "arrow"
				}
			],
			"updated": 1705733612758,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 3,
			"text": "abstract-machine/scripts/platform/nemu.mk",
			"rawText": "abstract-machine/scripts/platform/nemu.mk",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "abstract-machine/scripts/platform/nemu.mk",
			"lineHeight": 1.2,
			"baseline": 19
		},
		{
			"type": "rectangle",
			"version": 199,
			"versionNonce": 687162923,
			"isDeleted": false,
			"id": "WmvSCjvLoyVcY0tV5mJOV",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 600.5183003051216,
			"y": 1132.5692179879238,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 331.1400662893617,
			"height": 202.2125814635857,
			"seed": 432847592,
			"groupIds": [
				"odTKjQyNJzReqtMBVWGJK"
			],
			"frameId": null,
			"roundness": {
				"type": 3
			},
			"boundElements": [
				{
					"id": "51K6BNeAV8qDbDjS5glGo",
					"type": "arrow"
				}
			],
			"updated": 1689210237560,
			"link": null,
			"locked": false
		},
		{
			"type": "text",
			"version": 158,
			"versionNonce": 2033667743,
			"isDeleted": false,
			"id": "z5Jf7YQn",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 736.2314422269912,
			"y": 1149.5834007608923,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 58.59375,
			"height": 24,
			"seed": 662705560,
			"groupIds": [
				"Dqp1NNRFqOXH-0tA-x169",
				"odTKjQyNJzReqtMBVWGJK"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "UTCCg7mvj6SzuxmtfLbuh",
					"type": "arrow"
				},
				{
					"id": "fy5jV7W9bmR8Fn_6p4pX1",
					"type": "arrow"
				}
			],
			"updated": 1705733612758,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 3,
			"text": "image",
			"rawText": "image",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "image",
			"lineHeight": 1.2,
			"baseline": 19
		},
		{
			"type": "arrow",
			"version": 337,
			"versionNonce": 2053195979,
			"isDeleted": false,
			"id": "UTCCg7mvj6SzuxmtfLbuh",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 726.8826200230695,
			"y": 1179.1038253367215,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 80.62880766279056,
			"height": 106.82124302291527,
			"seed": 332036072,
			"groupIds": [
				"Dqp1NNRFqOXH-0tA-x169",
				"odTKjQyNJzReqtMBVWGJK"
			],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237560,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "z5Jf7YQn",
				"focus": 0.6627974679573809,
				"gap": 9.348822203921713
			},
			"endBinding": {
				"elementId": "GC4YQmw8",
				"focus": -0.33003031540385597,
				"gap": 5.64270844984253
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
					-80.62880766279056,
					106.82124302291527
				]
			]
		},
		{
			"type": "text",
			"version": 188,
			"versionNonce": 1403104977,
			"isDeleted": false,
			"id": "GC4YQmw8",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 624.1495506546506,
			"y": 1291.5677768094793,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 35.15625,
			"height": 24,
			"seed": 2063388904,
			"groupIds": [
				"Dqp1NNRFqOXH-0tA-x169",
				"odTKjQyNJzReqtMBVWGJK"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "UTCCg7mvj6SzuxmtfLbuh",
					"type": "arrow"
				}
			],
			"updated": 1705733612758,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 3,
			"text": "run",
			"rawText": "run",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "run",
			"lineHeight": 1.2,
			"baseline": 19
		},
		{
			"type": "arrow",
			"version": 425,
			"versionNonce": 1349777259,
			"isDeleted": false,
			"id": "fy5jV7W9bmR8Fn_6p4pX1",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 801.9328285012537,
			"y": 1175.1406875964158,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 59.68650717267193,
			"height": 116.36397623218818,
			"seed": 1490474648,
			"groupIds": [
				"Dqp1NNRFqOXH-0tA-x169",
				"odTKjQyNJzReqtMBVWGJK"
			],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237560,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "z5Jf7YQn",
				"focus": -0.8307163669166144,
				"gap": 7.107636274262404
			},
			"endBinding": {
				"elementId": "qXQ8U9Tm",
				"focus": 0.1130491980154395,
				"gap": 2.77737581931342
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
					59.68650717267193,
					116.36397623218818
				]
			]
		},
		{
			"type": "text",
			"version": 229,
			"versionNonce": 1941054143,
			"isDeleted": false,
			"id": "qXQ8U9Tm",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 848.9379334719858,
			"y": 1294.2820396479174,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 35.15625,
			"height": 24,
			"seed": 681303784,
			"groupIds": [
				"Dqp1NNRFqOXH-0tA-x169",
				"odTKjQyNJzReqtMBVWGJK"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "fy5jV7W9bmR8Fn_6p4pX1",
					"type": "arrow"
				}
			],
			"updated": 1705733612759,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 3,
			"text": "gdb",
			"rawText": "gdb",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "gdb",
			"lineHeight": 1.2,
			"baseline": 19
		},
		{
			"type": "arrow",
			"version": 233,
			"versionNonce": 964153867,
			"isDeleted": false,
			"id": "51K6BNeAV8qDbDjS5glGo",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 243.59273705060446,
			"y": 1228.4845341763785,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 335.2114605470181,
			"height": 7.053698446795693,
			"seed": 935818472,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237560,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "Z0gpk2Ha",
				"focus": -0.25424528863570983,
				"gap": 9.369874062329927
			},
			"endBinding": {
				"elementId": "WmvSCjvLoyVcY0tV5mJOV",
				"focus": -0.055489432881917704,
				"gap": 21.714102707498967
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
					335.2114605470181,
					7.053698446795693
				]
			]
		},
		{
			"type": "arrow",
			"version": 257,
			"versionNonce": 1070828337,
			"isDeleted": false,
			"id": "55IkphsiQ9DvoClBu8K1h",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 204.3639231522525,
			"y": 318.84266727820625,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 251.74853120402375,
			"height": 277.0145124401555,
			"seed": 276256664,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1705802076343,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "QbgoU5ygTXgCEN9ImVcWy",
				"gap": 9.770717820484606,
				"focus": -0.7565783964839286
			},
			"endBinding": {
				"elementId": "YHPhd_oib43FjhBUU4LAb",
				"gap": 3.902833925846153,
				"focus": -0.8837879745965459
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
					251.74853120402375,
					277.0145124401555
				]
			]
		},
		{
			"type": "rectangle",
			"version": 111,
			"versionNonce": 375871659,
			"isDeleted": false,
			"id": "YHPhd_oib43FjhBUU4LAb",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 459.7088402074023,
			"y": 597.3731353452044,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 610,
			"height": 44,
			"seed": 720904680,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 3
			},
			"boundElements": [
				{
					"id": "zYhuKyeF",
					"type": "text"
				},
				{
					"id": "55IkphsiQ9DvoClBu8K1h",
					"type": "arrow"
				}
			],
			"updated": 1689210237560,
			"link": null,
			"locked": false
		},
		{
			"type": "text",
			"version": 573,
			"versionNonce": 972749777,
			"isDeleted": false,
			"id": "zYhuKyeF",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 502.2088402074023,
			"y": 602.5731353452045,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 525,
			"height": 33.6,
			"seed": 376153320,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1705796956820,
			"link": null,
			"locked": false,
			"fontSize": 28,
			"fontFamily": 3,
			"text": "make -s -C $(AM_HOME)/am archive",
			"rawText": "make -s -C $(AM_HOME)/am archive",
			"textAlign": "center",
			"verticalAlign": "middle",
			"containerId": "YHPhd_oib43FjhBUU4LAb",
			"originalText": "make -s -C $(AM_HOME)/am archive",
			"lineHeight": 1.2,
			"baseline": 27
		},
		{
			"type": "rectangle",
			"version": 209,
			"versionNonce": 1156385611,
			"isDeleted": false,
			"id": "p9Z_n-Clevz0hYGZURgcv",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 475.6148211842626,
			"y": 78.16519166321928,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 646,
			"height": 45,
			"seed": 731418008,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 3
			},
			"boundElements": [
				{
					"id": "6bBIeX5W",
					"type": "text"
				},
				{
					"id": "JrzY3ZCS3Tg4bBdw7vw1i",
					"type": "arrow"
				}
			],
			"updated": 1689210237560,
			"link": null,
			"locked": false
		},
		{
			"type": "text",
			"version": 683,
			"versionNonce": 297491601,
			"isDeleted": false,
			"id": "6bBIeX5W",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 519.7085711842626,
			"y": 83.86519166321928,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 557.8125,
			"height": 33.6,
			"seed": 425925272,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1705796953986,
			"link": null,
			"locked": false,
			"fontSize": 28,
			"fontFamily": 3,
			"text": "make -s -C $(AM_HOME)/klib archive",
			"rawText": "make -s -C $(AM_HOME)/klib archive",
			"textAlign": "center",
			"verticalAlign": "middle",
			"containerId": "p9Z_n-Clevz0hYGZURgcv",
			"originalText": "make -s -C $(AM_HOME)/klib archive",
			"lineHeight": 1.2,
			"baseline": 27
		},
		{
			"type": "arrow",
			"version": 130,
			"versionNonce": 1121792753,
			"isDeleted": false,
			"id": "JrzY3ZCS3Tg4bBdw7vw1i",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 215.74813239877093,
			"y": 271.041854034134,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 250.46634629744418,
			"height": 175.42495439568938,
			"seed": 1093771672,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1705802076343,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "QbgoU5ygTXgCEN9ImVcWy",
				"gap": 4.143521297903874,
				"focus": 0.7926729515643496
			},
			"endBinding": {
				"elementId": "p9Z_n-Clevz0hYGZURgcv",
				"gap": 9.4003424880475,
				"focus": 0.9563064356711564
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
					250.46634629744418,
					-175.42495439568938
				]
			]
		},
		{
			"type": "text",
			"version": 116,
			"versionNonce": 1912974513,
			"isDeleted": false,
			"id": "SmddMurL",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 151.87521662421796,
			"y": 845.25690098323,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 1148.4375,
			"height": 240,
			"seed": 1680912280,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "R2MYEktX2OEGynAmk2hDl",
					"type": "arrow"
				}
			],
			"updated": 1705733612760,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 3,
			"text": "image: $(IMAGE).elf\n        @$(OBJDUMP) -d $(IMAGE).elf > $(IMAGE).txt\n        @echo + OBJCOPY \"->\" $(IMAGE_REL).bin\n        @$(OBJCOPY) -S --set-section-flags .bss=alloc,contents -O binary $(IMAGE).elf $(IMAGE).bin\n\nrun: image\n        $(MAKE) -C $(NEMU_HOME) ISA=$(ISA) run ARGS=\"$(NEMUFLAGS)\"\n\ngdb: image\n        $(MAKE) -C $(NEMU_HOME) ISA=$(ISA) gdb ARGS=\"$(NEMUFLAGS)\"",
			"rawText": "image: $(IMAGE).elf\n        @$(OBJDUMP) -d $(IMAGE).elf > $(IMAGE).txt\n        @echo + OBJCOPY \"->\" $(IMAGE_REL).bin\n        @$(OBJCOPY) -S --set-section-flags .bss=alloc,contents -O binary $(IMAGE).elf $(IMAGE).bin\n\nrun: image\n        $(MAKE) -C $(NEMU_HOME) ISA=$(ISA) run ARGS=\"$(NEMUFLAGS)\"\n\ngdb: image\n        $(MAKE) -C $(NEMU_HOME) ISA=$(ISA) gdb ARGS=\"$(NEMUFLAGS)\"",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "image: $(IMAGE).elf\n        @$(OBJDUMP) -d $(IMAGE).elf > $(IMAGE).txt\n        @echo + OBJCOPY \"->\" $(IMAGE_REL).bin\n        @$(OBJCOPY) -S --set-section-flags .bss=alloc,contents -O binary $(IMAGE).elf $(IMAGE).bin\n\nrun: image\n        $(MAKE) -C $(NEMU_HOME) ISA=$(ISA) run ARGS=\"$(NEMUFLAGS)\"\n\ngdb: image\n        $(MAKE) -C $(NEMU_HOME) ISA=$(ISA) gdb ARGS=\"$(NEMUFLAGS)\"",
			"lineHeight": 1.2,
			"baseline": 235
		},
		{
			"type": "arrow",
			"version": 41,
			"versionNonce": 953480331,
			"isDeleted": false,
			"id": "R2MYEktX2OEGynAmk2hDl",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 99.52991558074416,
			"y": 1207.937454101542,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 56.197495214954415,
			"height": 103.74922193530051,
			"seed": 18669032,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237560,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "Z0gpk2Ha",
				"focus": 0.3846565326590752,
				"gap": 7.63096323169043
			},
			"endBinding": {
				"elementId": "SmddMurL",
				"focus": 0.774558137994317,
				"gap": 18.93133118301148
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
					56.197495214954415,
					-103.74922193530051
				]
			]
		},
		{
			"type": "arrow",
			"version": 691,
			"versionNonce": 579513765,
			"isDeleted": false,
			"id": "4Q2AUADTzsUSSgnyv2onA",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1275.172932349514,
			"y": 824.6740469091342,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 1277.534240237844,
			"height": 886.1178573697885,
			"seed": 1721032680,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237560,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "NhOay6-CgUQqDWQ6QUeSs",
				"focus": 0.6264370209975522,
				"gap": 13.656804047899868
			},
			"endBinding": {
				"elementId": "haF_o66cQEtclYmBg1zsi",
				"focus": 0.7498209574333704,
				"gap": 13.15201979379799
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
					1277.534240237844,
					-886.1178573697885
				]
			]
		},
		{
			"type": "rectangle",
			"version": 212,
			"versionNonce": 586951467,
			"isDeleted": false,
			"id": "R4caPEezE6Q1o0AoDnOv7",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1226.1547660743893,
			"y": -929.1574007469732,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 1226.9526654444094,
			"height": 854.1863924279198,
			"seed": 795817880,
			"groupIds": [
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": {
				"type": 3
			},
			"boundElements": [],
			"updated": 1689210237560,
			"link": null,
			"locked": false
		},
		{
			"type": "text",
			"version": 421,
			"versionNonce": 1543336671,
			"isDeleted": false,
			"id": "WUGoJDkm",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1743.4589145546752,
			"y": -915.0539395795139,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 70.3125,
			"height": 24,
			"seed": 1815139224,
			"groupIds": [
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "Pcf7fTtr6Z39tMXQefTED",
					"type": "arrow"
				},
				{
					"id": "dpb0Ea6tKNm9fHZrcD0I5",
					"type": "arrow"
				}
			],
			"updated": 1705733612760,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 3,
			"text": "image ",
			"rawText": "image ",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "image ",
			"lineHeight": 1.2,
			"baseline": 19
		},
		{
			"type": "arrow",
			"version": 811,
			"versionNonce": 1011060171,
			"isDeleted": false,
			"id": "Pcf7fTtr6Z39tMXQefTED",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1574.0953785125246,
			"y": -595.9116728912553,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 176.01819776894058,
			"height": 280.3688172910239,
			"seed": 44360344,
			"groupIds": [
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237560,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "YRDS7gjI",
				"focus": -0.16863007934556265,
				"gap": 13.543005584204252
			},
			"endBinding": {
				"elementId": "WUGoJDkm",
				"focus": 0.2739042690100044,
				"gap": 14.773449397234685
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
					176.01819776894058,
					-280.3688172910239
				]
			]
		},
		{
			"type": "rectangle",
			"version": 271,
			"versionNonce": 1172129893,
			"isDeleted": false,
			"id": "3siJvAQ7ay4G133fD7Nrw",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1360.7102251778763,
			"y": -586.7097222657505,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 386.0179669593458,
			"height": 251.94302423682473,
			"seed": 1748439784,
			"groupIds": [
				"smKhAElxcQBGWHgkoIr9J",
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": {
				"type": 3
			},
			"boundElements": [
				{
					"id": "E9jZQrlh43FazTEhq4aSh",
					"type": "arrow"
				}
			],
			"updated": 1689210237560,
			"link": null,
			"locked": false
		},
		{
			"type": "text",
			"version": 261,
			"versionNonce": 49213073,
			"isDeleted": false,
			"id": "YRDS7gjI",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1515.487875352576,
			"y": -582.368667307051,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 105.46875,
			"height": 24,
			"seed": 390115992,
			"groupIds": [
				"smKhAElxcQBGWHgkoIr9J",
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "Pcf7fTtr6Z39tMXQefTED",
					"type": "arrow"
				},
				{
					"id": "KV2iFVnzBrvndYKeFo7_O",
					"type": "arrow"
				},
				{
					"id": "xlNP7qu-08uuXKDELkjuQ",
					"type": "arrow"
				},
				{
					"id": "4SVzAB3nXoki4qsfX9V0L",
					"type": "arrow"
				}
			],
			"updated": 1705733612761,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 3,
			"text": "image-dep",
			"rawText": "image-dep",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "image-dep",
			"lineHeight": 1.2,
			"baseline": 19
		},
		{
			"type": "arrow",
			"version": 766,
			"versionNonce": 1983968197,
			"isDeleted": false,
			"id": "KV2iFVnzBrvndYKeFo7_O",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1419.7370730342793,
			"y": -406.39748255909865,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 93.60570363999432,
			"height": 143.61821291844126,
			"seed": 1343015320,
			"groupIds": [
				"smKhAElxcQBGWHgkoIr9J",
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237560,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "BdLhhQo0",
				"focus": -0.2676411241865561,
				"gap": 8.092275254753417
			},
			"endBinding": {
				"elementId": "YRDS7gjI",
				"focus": 0.6872043944158049,
				"gap": 8.352971829511148
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
					93.60570363999432,
					-143.61821291844126
				]
			]
		},
		{
			"type": "text",
			"version": 289,
			"versionNonce": 447332095,
			"isDeleted": false,
			"id": "BdLhhQo0",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1378.6966990864587,
			"y": -398.30520730434523,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 82.03125,
			"height": 24,
			"seed": 1918777320,
			"groupIds": [
				"smKhAElxcQBGWHgkoIr9J",
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "KV2iFVnzBrvndYKeFo7_O",
					"type": "arrow"
				}
			],
			"updated": 1705733612761,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 3,
			"text": "$(OBJS)",
			"rawText": "$(OBJS)",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "$(OBJS)",
			"lineHeight": 1.2,
			"baseline": 19
		},
		{
			"type": "arrow",
			"version": 936,
			"versionNonce": 1742222117,
			"isDeleted": false,
			"id": "xlNP7qu-08uuXKDELkjuQ",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1558.9421698477406,
			"y": -401.2670574988199,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 5.444870220136181,
			"height": 143.67085525901177,
			"seed": 1801950616,
			"groupIds": [
				"smKhAElxcQBGWHgkoIr9J",
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237560,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "y7m6YyCv",
				"focus": 0.009986635597314664,
				"gap": 1.4884991755457122
			},
			"endBinding": {
				"elementId": "YRDS7gjI",
				"focus": 0.053985251870212254,
				"gap": 13.430754549219387
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
					5.444870220136181,
					-143.67085525901177
				]
			]
		},
		{
			"type": "text",
			"version": 372,
			"versionNonce": 219477105,
			"isDeleted": false,
			"id": "y7m6YyCv",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1546.5906570929121,
			"y": -399.7785583232742,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 23.4375,
			"height": 24,
			"seed": 885780632,
			"groupIds": [
				"smKhAElxcQBGWHgkoIr9J",
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "xlNP7qu-08uuXKDELkjuQ",
					"type": "arrow"
				}
			],
			"updated": 1705733612762,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 3,
			"text": "am",
			"rawText": "am",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "am",
			"lineHeight": 1.2,
			"baseline": 19
		},
		{
			"type": "arrow",
			"version": 966,
			"versionNonce": 1460700805,
			"isDeleted": false,
			"id": "4SVzAB3nXoki4qsfX9V0L",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1667.392728100106,
			"y": -400.7785583232737,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 39.358638162128045,
			"height": 146.46232414876272,
			"seed": 109192344,
			"groupIds": [
				"smKhAElxcQBGWHgkoIr9J",
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237560,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "UVLCQG5Q",
				"focus": -0.2118212158772924,
				"gap": 1
			},
			"endBinding": {
				"elementId": "YRDS7gjI",
				"focus": -0.9577838012892841,
				"gap": 11.127784835014609
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
					-39.358638162128045,
					-146.46232414876272
				]
			]
		},
		{
			"type": "text",
			"version": 402,
			"versionNonce": 842499871,
			"isDeleted": false,
			"id": "UVLCQG5Q",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1639.2416259068505,
			"y": -399.7785583232737,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 82.03125,
			"height": 24,
			"seed": 49991064,
			"groupIds": [
				"smKhAElxcQBGWHgkoIr9J",
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "4SVzAB3nXoki4qsfX9V0L",
					"type": "arrow"
				},
				{
					"id": "AvxT2IFPzH8j_KLSPzQhv",
					"type": "arrow"
				}
			],
			"updated": 1705733612762,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 3,
			"text": "$(LIBS)",
			"rawText": "$(LIBS)",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "$(LIBS)",
			"lineHeight": 1.2,
			"baseline": 19
		},
		{
			"type": "arrow",
			"version": 1019,
			"versionNonce": 380071397,
			"isDeleted": false,
			"id": "dpb0Ea6tKNm9fHZrcD0I5",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 2020.6587819354945,
			"y": -614.8766517375237,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 217.82526354140145,
			"height": 262.6886050638785,
			"seed": 365749992,
			"groupIds": [
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237560,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "B2nx7HowMA0TmmYJaaJAo",
				"focus": 0.14597007413360918,
				"gap": 17.14557321689574
			},
			"endBinding": {
				"elementId": "WUGoJDkm",
				"focus": -0.06834358722585535,
				"gap": 13.488682778111638
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
					-217.82526354140145,
					-262.6886050638785
				]
			]
		},
		{
			"type": "rectangle",
			"version": 326,
			"versionNonce": 473599723,
			"isDeleted": false,
			"id": "B2nx7HowMA0TmmYJaaJAo",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1902.9034001436758,
			"y": -597.731078520628,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 386.0179669593458,
			"height": 251.94302423682473,
			"seed": 1265206424,
			"groupIds": [
				"BUNxtoWiUi_4RbWq_Kk2a",
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": {
				"type": 3
			},
			"boundElements": [
				{
					"id": "dpb0Ea6tKNm9fHZrcD0I5",
					"type": "arrow"
				},
				{
					"id": "umuQm878XE01-OaVoeeY9",
					"type": "arrow"
				},
				{
					"id": "lxpocLA72jj45qkJWjElT",
					"type": "arrow"
				}
			],
			"updated": 1689210237560,
			"link": null,
			"locked": false
		},
		{
			"type": "text",
			"version": 326,
			"versionNonce": 1413430865,
			"isDeleted": false,
			"id": "e6xqDdQu",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 2057.681050318375,
			"y": -593.3900235619283,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 140.625,
			"height": 24,
			"seed": 570241432,
			"groupIds": [
				"BUNxtoWiUi_4RbWq_Kk2a",
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "yhtpatSXmyxK0fV1z5LhH",
					"type": "arrow"
				},
				{
					"id": "0rbvGdtfcSOwhQ5dpc4tY",
					"type": "arrow"
				},
				{
					"id": "tDLp1fVgoWa3UpJ0-tHbC",
					"type": "arrow"
				}
			],
			"updated": 1705733612762,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 3,
			"text": "$(IMAGE).elf",
			"rawText": "$(IMAGE).elf",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "$(IMAGE).elf",
			"lineHeight": 1.2,
			"baseline": 19
		},
		{
			"type": "arrow",
			"version": 951,
			"versionNonce": 260012427,
			"isDeleted": false,
			"id": "yhtpatSXmyxK0fV1z5LhH",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1962.254561172459,
			"y": -417.41883881397587,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 97.92051951104122,
			"height": 143.61821291844126,
			"seed": 596852376,
			"groupIds": [
				"BUNxtoWiUi_4RbWq_Kk2a",
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237561,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "hTpkA5Gx",
				"focus": -0.2713576077637563,
				"gap": 8.092275254753531
			},
			"endBinding": {
				"elementId": "e6xqDdQu",
				"focus": 0.6872043944157966,
				"gap": 8.352971829511148
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
					97.92051951104122,
					-143.61821291844126
				]
			]
		},
		{
			"type": "text",
			"version": 342,
			"versionNonce": 18303807,
			"isDeleted": false,
			"id": "hTpkA5Gx",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1920.8898740522582,
			"y": -409.32656355922234,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 82.03125,
			"height": 24,
			"seed": 14658456,
			"groupIds": [
				"BUNxtoWiUi_4RbWq_Kk2a",
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "yhtpatSXmyxK0fV1z5LhH",
					"type": "arrow"
				}
			],
			"updated": 1705733612762,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 3,
			"text": "$(OBJS)",
			"rawText": "$(OBJS)",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "$(OBJS)",
			"lineHeight": 1.2,
			"baseline": 19
		},
		{
			"type": "arrow",
			"version": 1121,
			"versionNonce": 739119147,
			"isDeleted": false,
			"id": "0rbvGdtfcSOwhQ5dpc4tY",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 2101.95258508153,
			"y": -412.288413753697,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 18.827611963054096,
			"height": 143.67085525901177,
			"seed": 873887896,
			"groupIds": [
				"BUNxtoWiUi_4RbWq_Kk2a",
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237561,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "DenlaT2q",
				"focus": -0.023896978989107844,
				"gap": 1.4884991755457122
			},
			"endBinding": {
				"elementId": "e6xqDdQu",
				"focus": 0.0539852518702163,
				"gap": 13.4307545492195
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
					18.827611963054096,
					-143.67085525901177
				]
			]
		},
		{
			"type": "text",
			"version": 425,
			"versionNonce": 927288369,
			"isDeleted": false,
			"id": "DenlaT2q",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 2088.7838320587116,
			"y": -410.7999145781513,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 23.4375,
			"height": 24,
			"seed": 1357620632,
			"groupIds": [
				"BUNxtoWiUi_4RbWq_Kk2a",
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "0rbvGdtfcSOwhQ5dpc4tY",
					"type": "arrow"
				}
			],
			"updated": 1705733612762,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 3,
			"text": "am",
			"rawText": "am",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "am",
			"lineHeight": 1.2,
			"baseline": 19
		},
		{
			"type": "arrow",
			"version": 1151,
			"versionNonce": 1943065291,
			"isDeleted": false,
			"id": "tDLp1fVgoWa3UpJ0-tHbC",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 2211.382583503495,
			"y": -411.7999145781513,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 12.977296917448257,
			"height": 146.4627666462036,
			"seed": 1418932888,
			"groupIds": [
				"BUNxtoWiUi_4RbWq_Kk2a",
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237561,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "cOh8lggy",
				"focus": -0.23565218792998985,
				"gap": 1.0000000000004547
			},
			"endBinding": {
				"elementId": "e6xqDdQu",
				"focus": -0.9577838012892775,
				"gap": 11.127342337573396
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
					-12.977296917448257,
					-146.4627666462036
				]
			]
		},
		{
			"type": "text",
			"version": 454,
			"versionNonce": 1135184735,
			"isDeleted": false,
			"id": "cOh8lggy",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 2181.43480087265,
			"y": -410.79991457815083,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 82.03125,
			"height": 24,
			"seed": 1975590808,
			"groupIds": [
				"BUNxtoWiUi_4RbWq_Kk2a",
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "tDLp1fVgoWa3UpJ0-tHbC",
					"type": "arrow"
				}
			],
			"updated": 1705733612762,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 3,
			"text": "$(LIBS)",
			"rawText": "$(LIBS)",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "$(LIBS)",
			"lineHeight": 1.2,
			"baseline": 19
		},
		{
			"type": "arrow",
			"version": 671,
			"versionNonce": 569371313,
			"isDeleted": false,
			"id": "E9jZQrlh43FazTEhq4aSh",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1541.176363926134,
			"y": -323.7886632189791,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 2.2671719063341698,
			"height": 131.81563751389444,
			"seed": 697882344,
			"groupIds": [
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1705802076343,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "3siJvAQ7ay4G133fD7Nrw",
				"gap": 10.978034809946735,
				"focus": 0.07633287502905094
			},
			"endBinding": {
				"elementId": "Le9NHE842IjP70KkJhNNj",
				"gap": 3.272727272727252,
				"focus": -0.11566265060241229
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
					2.2671719063341698,
					131.81563751389444
				]
			]
		},
		{
			"type": "rectangle",
			"version": 274,
			"versionNonce": 132980421,
			"isDeleted": false,
			"id": "Le9NHE842IjP70KkJhNNj",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1343.0038792645103,
			"y": -188.70029843235739,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#a5d8ff",
			"width": 455,
			"height": 72,
			"seed": 2115779480,
			"groupIds": [
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": {
				"type": 3
			},
			"boundElements": [
				{
					"id": "E9jZQrlh43FazTEhq4aSh",
					"type": "arrow"
				},
				{
					"type": "text",
					"id": "TeMYjIe3"
				}
			],
			"updated": 1689210237561,
			"link": null,
			"locked": false
		},
		{
			"type": "text",
			"version": 224,
			"versionNonce": 537997233,
			"isDeleted": false,
			"id": "TeMYjIe3",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1480.5038792645103,
			"y": -164.70029843235739,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#a5d8ff",
			"width": 180,
			"height": 24,
			"seed": 592725992,
			"groupIds": [
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1705733594618,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 3,
			"text": "主要是输出相关信息",
			"rawText": "主要是输出相关信息",
			"textAlign": "center",
			"verticalAlign": "middle",
			"containerId": "Le9NHE842IjP70KkJhNNj",
			"originalText": "主要是输出相关信息",
			"lineHeight": 1.2,
			"baseline": 19
		},
		{
			"type": "rectangle",
			"version": 321,
			"versionNonce": 1757871653,
			"isDeleted": false,
			"id": "nxv98MJVSDFxlFgfIzJ-C",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1916.361868702429,
			"y": -187.83185122259033,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#a5d8ff",
			"width": 455,
			"height": 72,
			"seed": 2141755800,
			"groupIds": [
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": {
				"type": 3
			},
			"boundElements": [
				{
					"type": "text",
					"id": "41RWyTm3"
				},
				{
					"id": "umuQm878XE01-OaVoeeY9",
					"type": "arrow"
				}
			],
			"updated": 1689210237561,
			"link": null,
			"locked": false
		},
		{
			"type": "text",
			"version": 290,
			"versionNonce": 833986897,
			"isDeleted": false,
			"id": "41RWyTm3",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 2083.861868702429,
			"y": -163.83185122259033,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#a5d8ff",
			"width": 120,
			"height": 24,
			"seed": 126985880,
			"groupIds": [
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1705733594618,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 3,
			"text": "执行链接操作",
			"rawText": "执行链接操作",
			"textAlign": "center",
			"verticalAlign": "middle",
			"containerId": "nxv98MJVSDFxlFgfIzJ-C",
			"originalText": "执行链接操作",
			"lineHeight": 1.2,
			"baseline": 19
		},
		{
			"type": "arrow",
			"version": 543,
			"versionNonce": 436712049,
			"isDeleted": false,
			"id": "umuQm878XE01-OaVoeeY9",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 2105.415123054988,
			"y": -337.41183730375707,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#a5d8ff",
			"width": 16.71597636845263,
			"height": 143.75739676869108,
			"seed": 1189953432,
			"groupIds": [
				"QMbXo77OOVJxtuqg07Jvw",
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1705802076344,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "B2nx7HowMA0TmmYJaaJAo",
				"gap": 8.376216980046252,
				"focus": 0.02946731597271622
			},
			"endBinding": {
				"elementId": "nxv98MJVSDFxlFgfIzJ-C",
				"gap": 5.822589312475657,
				"focus": -0.07280402834972456
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
					16.71597636845263,
					143.75739676869108
				]
			]
		},
		{
			"type": "text",
			"version": 157,
			"versionNonce": 1309580817,
			"isDeleted": false,
			"id": "2Wm9oysd",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1294.6902691850444,
			"y": -878.7620303397355,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 164.0625,
			"height": 33.6,
			"seed": 221517800,
			"groupIds": [
				"ENqMBppwqqyvtd52cUPHD"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1705733612763,
			"link": null,
			"locked": false,
			"fontSize": 28,
			"fontFamily": 3,
			"text": "make image",
			"rawText": "make image",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "make image",
			"lineHeight": 1.2,
			"baseline": 27
		},
		{
			"type": "rectangle",
			"version": 328,
			"versionNonce": 2090825957,
			"isDeleted": false,
			"id": "wkS4w7fv5cRsHqeWxewW7",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1664.6539526035801,
			"y": 674.5014983539683,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 990.9209950466145,
			"height": 630.5774415247458,
			"seed": 1537193368,
			"groupIds": [
				"KSHItfWcCCbqy3y41kN5N"
			],
			"frameId": null,
			"roundness": {
				"type": 3
			},
			"boundElements": [],
			"updated": 1689210237561,
			"link": null,
			"locked": false
		},
		{
			"type": "text",
			"version": 237,
			"versionNonce": 1446954879,
			"isDeleted": false,
			"id": "ZqwgvBri",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1708.344016724994,
			"y": 718.6855090138959,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 196.875,
			"height": 33.6,
			"seed": 912779160,
			"groupIds": [
				"KSHItfWcCCbqy3y41kN5N"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1705733612763,
			"link": null,
			"locked": false,
			"fontSize": 28,
			"fontFamily": 3,
			"text": "make archive",
			"rawText": "make archive",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "make archive",
			"lineHeight": 1.2,
			"baseline": 27
		},
		{
			"type": "text",
			"version": 562,
			"versionNonce": 1200796657,
			"isDeleted": false,
			"id": "td6n4hRq",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1852.7560344764152,
			"y": 855.6525791970155,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 114.84375,
			"height": 33.6,
			"seed": 239420056,
			"groupIds": [
				"UstF6xqjHxpzU4K4Eg8Na",
				"KSHItfWcCCbqy3y41kN5N"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "wdG-7gnKgoHSZd--0OAUI",
					"type": "arrow"
				},
				{
					"id": "AvxT2IFPzH8j_KLSPzQhv",
					"type": "arrow"
				},
				{
					"id": "lxpocLA72jj45qkJWjElT",
					"type": "arrow"
				}
			],
			"updated": 1705733612763,
			"link": null,
			"locked": false,
			"fontSize": 28,
			"fontFamily": 3,
			"text": "archive",
			"rawText": "archive",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "archive",
			"lineHeight": 1.2,
			"baseline": 27
		},
		{
			"type": "arrow",
			"version": 1520,
			"versionNonce": 1603600011,
			"isDeleted": false,
			"id": "wdG-7gnKgoHSZd--0OAUI",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1898.1590278574868,
			"y": 1042.614031840108,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 2.5647097144974396,
			"height": 146.74322311408457,
			"seed": 1994351768,
			"groupIds": [
				"UstF6xqjHxpzU4K4Eg8Na",
				"KSHItfWcCCbqy3y41kN5N"
			],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237561,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "G9wtN7WM",
				"focus": -0.38419868994028383,
				"gap": 3.100059781361324
			},
			"endBinding": {
				"elementId": "td6n4hRq",
				"focus": 0.2597722426867952,
				"gap": 6.618229529008033
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
					-2.5647097144974396,
					-146.74322311408457
				]
			]
		},
		{
			"type": "text",
			"version": 632,
			"versionNonce": 924286879,
			"isDeleted": false,
			"id": "G9wtN7WM",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1848.1046900280412,
			"y": 1045.7140916214694,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 164.0625,
			"height": 33.6,
			"seed": 879702424,
			"groupIds": [
				"UstF6xqjHxpzU4K4Eg8Na",
				"KSHItfWcCCbqy3y41kN5N"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "wdG-7gnKgoHSZd--0OAUI",
					"type": "arrow"
				},
				{
					"id": "rcUFUqqOUtE-3XfC7DAZS",
					"type": "arrow"
				}
			],
			"updated": 1705733612764,
			"link": null,
			"locked": false,
			"fontSize": 28,
			"fontFamily": 3,
			"text": "$(ARCHIVE)",
			"rawText": "$(ARCHIVE)",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "$(ARCHIVE)",
			"lineHeight": 1.2,
			"baseline": 27
		},
		{
			"type": "text",
			"version": 689,
			"versionNonce": 131665361,
			"isDeleted": false,
			"id": "c0yuOLfO",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1874.006083259214,
			"y": 1225.8435242934704,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 114.84374999999999,
			"height": 33.599999999999994,
			"seed": 2071482008,
			"groupIds": [
				"UstF6xqjHxpzU4K4Eg8Na",
				"KSHItfWcCCbqy3y41kN5N"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "rcUFUqqOUtE-3XfC7DAZS",
					"type": "arrow"
				},
				{
					"id": "aIrV7mEBjDLpt7g0ZvlRv",
					"type": "arrow"
				},
				{
					"id": "w5ULhjJB9ApXcJRddKLw7",
					"type": "arrow"
				}
			],
			"updated": 1705733612764,
			"link": null,
			"locked": false,
			"fontSize": 28,
			"fontFamily": 3,
			"text": "$(OBJS)",
			"rawText": "$(OBJS)",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "$(OBJS)",
			"lineHeight": 1.2,
			"baseline": 27
		},
		{
			"type": "arrow",
			"version": 1663,
			"versionNonce": 1795852037,
			"isDeleted": false,
			"id": "rcUFUqqOUtE-3XfC7DAZS",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1913.5167563953219,
			"y": 1216.5157942001024,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "#ffc9c9",
			"width": 4.326955207865467,
			"height": 134.3205036194637,
			"seed": 1161856408,
			"groupIds": [
				"UstF6xqjHxpzU4K4Eg8Na",
				"KSHItfWcCCbqy3y41kN5N"
			],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237561,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "c0yuOLfO",
				"focus": -0.29448981279358294,
				"gap": 9.327730093368018
			},
			"endBinding": {
				"elementId": "G9wtN7WM",
				"focus": 0.26134800480376935,
				"gap": 2.8811989591695237
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
					-4.326955207865467,
					-134.3205036194637
				]
			]
		},
		{
			"type": "arrow",
			"version": 153,
			"versionNonce": 101259211,
			"isDeleted": false,
			"id": "aIrV7mEBjDLpt7g0ZvlRv",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1992.6429774832145,
			"y": 1241.003157544943,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 169.77716642648375,
			"height": 1.4239506905923918,
			"seed": 2087125480,
			"groupIds": [
				"KSHItfWcCCbqy3y41kN5N"
			],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237561,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "c0yuOLfO",
				"focus": -0.06521070021154818,
				"gap": 3.793144224000571
			},
			"endBinding": {
				"elementId": "WpVpxfNp",
				"focus": -0.3949873401487926,
				"gap": 10.352266245517967
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
					169.77716642648375,
					-1.4239506905923918
				]
			]
		},
		{
			"type": "text",
			"version": 90,
			"versionNonce": 1214526399,
			"isDeleted": false,
			"id": "WpVpxfNp",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 2172.772410155216,
			"y": 1213.657178806022,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 410.15625,
			"height": 33.6,
			"seed": 271010968,
			"groupIds": [
				"KSHItfWcCCbqy3y41kN5N"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "aIrV7mEBjDLpt7g0ZvlRv",
					"type": "arrow"
				}
			],
			"updated": 1705733612764,
			"link": null,
			"locked": false,
			"fontSize": 28,
			"fontFamily": 3,
			"text": "ar rcs $(ARCHIVE) $(OBJS)",
			"rawText": "ar rcs $(ARCHIVE) $(OBJS)",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "ar rcs $(ARCHIVE) $(OBJS)",
			"lineHeight": 1.2,
			"baseline": 27
		},
		{
			"type": "arrow",
			"version": 93,
			"versionNonce": 1414129259,
			"isDeleted": false,
			"id": "AvxT2IFPzH8j_KLSPzQhv",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1897.339561083738,
			"y": 839.7639042117105,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 217.40450873354234,
			"height": 1202.5186889324052,
			"seed": 2036858539,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237561,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "td6n4hRq",
				"focus": -0.11459853373495205,
				"gap": 15.888674985304931
			},
			"endBinding": {
				"elementId": "UVLCQG5Q",
				"focus": 0.11222085316233317,
				"gap": 13.02377360257907
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
					-217.40450873354234,
					-1202.5186889324052
				]
			]
		},
		{
			"type": "arrow",
			"version": 183,
			"versionNonce": 1518225861,
			"isDeleted": false,
			"id": "lxpocLA72jj45qkJWjElT",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1942.2772093884273,
			"y": 854.3117591170419,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 260.4324844203884,
			"height": 1184.4016465379434,
			"seed": 1645105419,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237561,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "td6n4hRq",
				"focus": 0.45995197221954154,
				"gap": 1.3408200799735255
			},
			"endBinding": {
				"elementId": "B2nx7HowMA0TmmYJaaJAo",
				"focus": -0.6250259238540682,
				"gap": 15.698166862901815
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
					260.4324844203884,
					-1184.4016465379434
				]
			]
		},
		{
			"type": "arrow",
			"version": 73,
			"versionNonce": 1253564683,
			"isDeleted": false,
			"id": "w5ULhjJB9ApXcJRddKLw7",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1931.6084471298957,
			"y": 1518.5803420383884,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 19.71298024209159,
			"height": 258.0343907263773,
			"seed": 2003469483,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237561,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "KImVYLci",
				"focus": -0.10132055048282834,
				"gap": 10.604153043549786
			},
			"endBinding": {
				"elementId": "c0yuOLfO",
				"focus": 0.3560183464249789,
				"gap": 1.1024270185407659
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
					-19.71298024209159,
					-258.0343907263773
				]
			]
		},
		{
			"type": "text",
			"version": 63,
			"versionNonce": 100215729,
			"isDeleted": false,
			"id": "KImVYLci",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1388.3297971660222,
			"y": 1529.1844950819382,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 1214.0625,
			"height": 33.6,
			"seed": 1545867883,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "w5ULhjJB9ApXcJRddKLw7",
					"type": "arrow"
				},
				{
					"id": "8ZvQN7fjeAAIXRaecy-b7",
					"type": "arrow"
				}
			],
			"updated": 1705733612764,
			"link": null,
			"locked": false,
			"fontSize": 28,
			"fontFamily": 3,
			"text": "OBJS      = $(addprefix $(DST_DIR)/, $(addsuffix .o, $(basename $(SRCS))))",
			"rawText": "OBJS      = $(addprefix $(DST_DIR)/, $(addsuffix .o, $(basename $(SRCS))))",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "OBJS      = $(addprefix $(DST_DIR)/, $(addsuffix .o, $(basename $(SRCS))))",
			"lineHeight": 1.2,
			"baseline": 27
		},
		{
			"type": "arrow",
			"version": 67,
			"versionNonce": 1120765867,
			"isDeleted": false,
			"id": "8ZvQN7fjeAAIXRaecy-b7",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1967.7801384096804,
			"y": 1811.9619095765986,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 29.586825540216296,
			"height": 235.05872579868628,
			"seed": 57088421,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237561,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "0rHVoPdR",
				"focus": -0.002414179454251941,
				"gap": 10.604153043550014
			},
			"endBinding": {
				"elementId": "KImVYLci",
				"focus": 0.10023784289859428,
				"gap": 14.118688695974015
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
					-29.586825540216296,
					-235.05872579868628
				]
			]
		},
		{
			"type": "text",
			"version": 53,
			"versionNonce": 1380279263,
			"isDeleted": false,
			"id": "0rHVoPdR",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1635.76003484885,
			"y": 1822.5660626201484,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 672.65625,
			"height": 33.6,
			"seed": 450551173,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "8ZvQN7fjeAAIXRaecy-b7",
					"type": "arrow"
				},
				{
					"id": "pF-eZzTMgwH14_4JPpNrm",
					"type": "arrow"
				}
			],
			"updated": 1705733612765,
			"link": null,
			"locked": false,
			"fontSize": 28,
			"fontFamily": 3,
			"text": "SRCS      = $(addprefix src/, $(AM_SRCS))",
			"rawText": "SRCS      = $(addprefix src/, $(AM_SRCS))",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "SRCS      = $(addprefix src/, $(AM_SRCS))",
			"lineHeight": 1.2,
			"baseline": 27
		},
		{
			"type": "text",
			"version": 54,
			"versionNonce": 1780125073,
			"isDeleted": false,
			"id": "FmKgTyuM",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1754.4266360473518,
			"y": 2041.601048352823,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 557.8125,
			"height": 403.20000000000005,
			"seed": 322938277,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "pF-eZzTMgwH14_4JPpNrm",
					"type": "arrow"
				}
			],
			"updated": 1705733612766,
			"link": null,
			"locked": false,
			"fontSize": 28,
			"fontFamily": 3,
			"text": "AM_SRCS := native/trm.c \\\n           native/ioe.c \\\n           native/cte.c \\\n           native/trap.S \\\n           native/vme.c \\\n           native/mpe.c \\\n           native/platform.c \\\n           native/native-input.c \\\n           native/native-timer.c \\\n           native/native-gpu.c \\\n           native/native-audio.c \\\n",
			"rawText": "AM_SRCS := native/trm.c \\\n           native/ioe.c \\\n           native/cte.c \\\n           native/trap.S \\\n           native/vme.c \\\n           native/mpe.c \\\n           native/platform.c \\\n           native/native-input.c \\\n           native/native-timer.c \\\n           native/native-gpu.c \\\n           native/native-audio.c \\\n",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "AM_SRCS := native/trm.c \\\n           native/ioe.c \\\n           native/cte.c \\\n           native/trap.S \\\n           native/vme.c \\\n           native/mpe.c \\\n           native/platform.c \\\n           native/native-input.c \\\n           native/native-timer.c \\\n           native/native-gpu.c \\\n           native/native-audio.c \\\n",
			"lineHeight": 1.2,
			"baseline": 396
		},
		{
			"type": "arrow",
			"version": 62,
			"versionNonce": 1612274949,
			"isDeleted": false,
			"id": "pF-eZzTMgwH14_4JPpNrm",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 1975.1447155681594,
			"y": 2019.662011431235,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 3.0098414329718253,
			"height": 157.22976460471864,
			"seed": 359945829,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1689210237562,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "FmKgTyuM",
				"focus": -0.21750511662267732,
				"gap": 21.939036921587785
			},
			"endBinding": {
				"elementId": "0rHVoPdR",
				"focus": -0.019331523054567507,
				"gap": 6.266184206368052
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
					3.0098414329718253,
					-157.22976460471864
				]
			]
		},
		{
			"type": "text",
			"version": 59,
			"versionNonce": 480486449,
			"isDeleted": false,
			"id": "FsFOITw4",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 2467.445335998983,
			"y": 2205.000331418337,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 233.8199462890625,
			"height": 43.199999999999996,
			"seed": 976861221,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1705801954197,
			"link": null,
			"locked": false,
			"fontSize": 36,
			"fontFamily": 4,
			"text": "在native.mk中",
			"rawText": "在native.mk中",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "在native.mk中",
			"lineHeight": 1.2,
			"baseline": 35
		},
		{
			"type": "text",
			"version": 36,
			"versionNonce": 737981279,
			"isDeleted": false,
			"id": "gnPS2zPk",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 2423.5672621558047,
			"y": 1840.4932099049279,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 346.46392822265625,
			"height": 43.199999999999996,
			"seed": 1437380389,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [
				{
					"id": "tyrEhPzhCPSoMYhD6GiNI",
					"type": "arrow"
				}
			],
			"updated": 1705801954198,
			"link": null,
			"locked": false,
			"fontSize": 36,
			"fontFamily": 4,
			"text": "在am/下的makefile中",
			"rawText": "在am/下的makefile中",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "在am/下的makefile中",
			"lineHeight": 1.2,
			"baseline": 35
		},
		{
			"type": "arrow",
			"version": 196,
			"versionNonce": 944890469,
			"isDeleted": false,
			"id": "tyrEhPzhCPSoMYhD6GiNI",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 2989.249182665077,
			"y": -122.17280176061445,
			"strokeColor": "#e03131",
			"backgroundColor": "transparent",
			"width": 296.75339985003166,
			"height": 1955.0325169544874,
			"seed": 1119503813,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [
				{
					"type": "text",
					"id": "YsuoZVAX"
				}
			],
			"updated": 1689210259530,
			"link": null,
			"locked": false,
			"startBinding": null,
			"endBinding": {
				"elementId": "gnPS2zPk",
				"focus": 0.5810990226605054,
				"gap": 7.633494711054823
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
					-296.75339985003166,
					1955.0325169544874
				]
			]
		},
		{
			"type": "text",
			"version": 71,
			"versionNonce": 1704197483,
			"isDeleted": false,
			"id": "YsuoZVAX",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 2775.9687709444797,
			"y": 819.624634864109,
			"strokeColor": "#e03131",
			"backgroundColor": "transparent",
			"width": 216,
			"height": 86.39999999999999,
			"seed": 92611307,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1689210258137,
			"link": null,
			"locked": false,
			"fontSize": 36,
			"fontFamily": 4,
			"text": "通过这个规则\n调用",
			"rawText": "通过这个规则调用",
			"textAlign": "center",
			"verticalAlign": "middle",
			"containerId": "tyrEhPzhCPSoMYhD6GiNI",
			"originalText": "通过这个规则调用",
			"lineHeight": 1.2,
			"baseline": 78
		}
	],
	"appState": {
		"theme": "light",
		"viewBackgroundColor": "#ffffff",
		"currentItemStrokeColor": "#e03131",
		"currentItemBackgroundColor": "transparent",
		"currentItemFillStyle": "hachure",
		"currentItemStrokeWidth": 1,
		"currentItemStrokeStyle": "solid",
		"currentItemRoughness": 1,
		"currentItemOpacity": 100,
		"currentItemFontFamily": 4,
		"currentItemFontSize": 36,
		"currentItemTextAlign": "left",
		"currentItemStartArrowhead": null,
		"currentItemEndArrowhead": "triangle",
		"scrollX": 254.87755066641301,
		"scrollY": 1334.3575589855297,
		"zoom": {
			"value": 0.45
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