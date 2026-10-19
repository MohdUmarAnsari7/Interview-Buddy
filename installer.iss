[Setup]
AppName=Interview Buddy
AppVersion=1.0.0
DefaultDirName={autopf}\Interview Buddy
DefaultGroupName=Interview Buddy
OutputDir=installer
OutputBaseFilename=InterviewBuddy-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=InterviewBuddy.ico

PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Files]
Source: "dist\InterviewBuddy\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\Interview Buddy"; Filename: "{app}\InterviewBuddy.exe"; IconFilename: "{app}\InterviewBuddy.exe"
Name: "{autodesktop}\Interview Buddy"; Filename: "{app}\InterviewBuddy.exe"; IconFilename: "{app}\InterviewBuddy.exe"

[Run]
Filename: "{app}\InterviewBuddy.exe"; Description: "Launch Interview Buddy"; Flags: nowait postinstall skipifsilent