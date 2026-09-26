; Inno Setup script — OpenJyotish Windows installer.
; Built on CI (choco install innosetup): iscc packaging\windows\OpenJyotish.iss
#define MyAppName "OpenJyotish"
#define MyAppVersion GetEnv("APP_VERSION")
#define MyAppPublisher "OpenJyotish Contributors"
#define MyAppURL "https://github.com/velteyn/OpenJyotish"
#define MyAppExeName "OpenJyotish.exe"

[Setup]
AppId={{8E2B4F1A-7C3D-4A9B-9F2E-1A2B3C4D5E6F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\OpenJyotish
DefaultGroupName=OpenJyotish
LicenseFile=..\..\LICENSE
OutputDir=..\..\dist-installer
OutputBaseFilename=OpenJyotish-{#MyAppVersion}-Windows-Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\OpenJyotish\*"; DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\OpenJyotish"; Filename: "{app}\{#MyAppExeName}"
; TUI via a persistent console: bare openjyotish.exe with no command
; exits immediately (which just flashes and closes when double-clicked),
; so open cmd, start the terminal UI, and stay open in the install dir.
Name: "{group}\OpenJyotish TUI"; Filename: "{cmd}"; \
    Parameters: "/K openjyotish.exe tui"; WorkingDir: "{app}"
Name: "{autodesktop}\OpenJyotish"; Filename: "{app}\{#MyAppExeName}"; \
    Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; \
    Description: "{cm:LaunchProgram,OpenJyotish}"; \
    Flags: nowait postinstall skipifsilent
