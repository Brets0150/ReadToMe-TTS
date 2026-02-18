; Inno Setup Script for ReadToMe-TTS
; Download Inno Setup from: https://jrsoftware.org/isinfo.php
;
; To compile: open this file in Inno Setup Compiler and click Build > Compile
; Or from command line: iscc installer\ReadToMe_Setup.iss

#define MyAppName "ReadToMe"
#define MyAppVersion "0.2.0"
#define MyAppPublisher "ReadToMe"
#define MyAppExeName "ReadToMe.exe"
#define MyAppDescription "Highlight text anywhere and hear it read aloud"

[Setup]
AppId={{B8F3A1E2-7C4D-4E5F-9A1B-2C3D4E5F6A7B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppSupportURL=https://github.com/CyberGladius/ReadToMe-TTS
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; No license page — remove or set LicenseFile if you add a LICENSE
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=ReadToMe_Setup_{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; Require admin for Program Files install
PrivilegesRequired=admin
; Minimum Windows 10
MinVersion=10.0
; Uninstall icon
UninstallDisplayIcon={app}\{#MyAppExeName}
; App description in Add/Remove Programs
AppComments={#MyAppDescription}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupentry"; Description: "Start ReadToMe when Windows starts"; GroupDescription: "Startup:"

[Files]
; Copy entire PyInstaller output directory
Source: "..\dist\ReadToMe\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "{#MyAppDescription}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
; Desktop shortcut (optional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Comment: "{#MyAppDescription}"

[Registry]
; Add to Windows startup if selected
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: startupentry

[Run]
; Option to launch after install
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Kill the app before uninstalling
Filename: "taskkill"; Parameters: "/F /IM {#MyAppExeName}"; Flags: runhidden; RunOnceId: "KillApp"
