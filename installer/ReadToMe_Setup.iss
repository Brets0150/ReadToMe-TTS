; Inno Setup Script for ReadToMe-TTS
; Download Inno Setup from: https://jrsoftware.org/isinfo.php
;
; To compile: open this file in Inno Setup Compiler and click Build > Compile
; Or from command line: iscc installer\ReadToMe_Setup.iss

#define MyAppName "ReadToMe"
#define MyAppVersion "0.3.0"
#define MyAppPublisher "ReadToMe"
#define MyAppExeName "ReadToMe.exe"
#define MyAppDescription "Highlight text anywhere and hear it read aloud"

; Minimum VC++ Redistributable version required (14.40 = VS 2015-2022 latest)
#define VCRedistMinVersion "14.40"

[Setup]
AppId={{B8F3A1E2-7C4D-4E5F-9A1B-2C3D4E5F6A7B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppSupportURL=https://github.com/Brets0150/ReadToMe-TTS
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
; 64-bit application — install to Program Files, not Program Files (x86)
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
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
; Microsoft Visual C++ Redistributable (required by Python and onnxruntime)
Source: "..\redist\vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall
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
; Install VC++ Redistributable silently (skips if already installed or newer)
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "Installing Microsoft Visual C++ Runtime..."; Flags: waituntilterminated; Check: VCRedistNeedsInstall
; Option to launch after install
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Kill the app before uninstalling
Filename: "taskkill"; Parameters: "/F /IM {#MyAppExeName}"; Flags: runhidden; RunOnceId: "KillApp"

[UninstallDelete]
; Clean up user config directory
Type: files; Name: "{%USERPROFILE}\.readtome\config.json"
Type: files; Name: "{%USERPROFILE}\.readtome\readtome.log"
Type: dirifempty; Name: "{%USERPROFILE}\.readtome"

[Code]
// Check if the VC++ 2015-2022 Redistributable (x64) is already installed.
// The installer sets Installed=1 under this registry key.
function VCRedistNeedsInstall: Boolean;
var
  Installed: Cardinal;
begin
  Result := True;
  if RegQueryDWordValue(HKLM, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Installed', Installed) then
  begin
    if Installed = 1 then
      Result := False;
  end;
end;
