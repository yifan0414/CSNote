# c_cpp_properties.json
```json
{
    "configurations": [
        {
            "name": "Linux",
            "includePath": [
                "${workspaceFolder}/**"
            ],
            "defines": [
                "__ISA__=x86",
                "__ISA_x86__",
                "_ISA_H_=\"isa/x86.h\""
            ],
            "compilerPath": "/usr/bin/gcc",
            "intelliSenseMode": "linux-gcc-x64",
            "configurationProvider": "ms-vscode.makefile-tools"
        }
    ],
    "version": 4
}
```

# tasks.json
```json
{
	"version": "2.0.0",
	"tasks": [
		{
			"type": "shell",
			"label": "make",
			"command": "make -j8",
			"args": [],
			"options": {},
			"problemMatcher": [],
			"group": {
				"kind": "build",
				"isDefault": true
			},
		}
	]
}
```

# launch.json
```json
{
    // 使用 IntelliSense 了解相关属性。 
    // 悬停以查看现有属性的描述。
    // 欲了解更多信息，请访问: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": "(gdb) Launch",
            "type": "cppdbg",
            "request": "launch",
            "program": "/home/yifansu/ics2020/nemu/build/riscv32-nemu-interpreter",
            "args": [ "-b" ],
            "stopAtEntry": false,
            "cwd": "${workspaceRoot}",
            "environment": [],
            "externalConsole": false,
            "MIMode": "gdb",
            "setupCommands": [
                {
                    "description": "Enable pre",
                    "text": "-enable-pretty-print",
                    "ignoreFailures": true
                }
            ]
        }
    ]
}
```