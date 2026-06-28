#import <Cocoa/Cocoa.h>

#define DEFAULT_CORPID    @"wwedd915ec24199490"
#define DEFAULT_SECRET    @""
#define CHECK_INTERVAL    300

@interface AppDelegate : NSObject <NSApplicationDelegate>
@property (strong) NSWindow *window;
@property (strong) NSTextField *ipLabel;
@property (strong) NSTextField *statusLabel;
@property (strong) NSTextField *timeLabel;
@property (strong) NSTextField *configLabel;
@property (strong) NSButton *toggleBtn;
@property (strong) NSTextField *corpIDField;
@property (strong) NSTextField *secretField;
@property (strong) NSTextField *intervalField;
@property (strong) NSView *configView;
@property (strong) NSStatusItem *statusItem;
@property (strong) NSTimer *checkTimer;
@property (strong) NSString *corpID;
@property (strong) NSString *corpSecret;
@property (assign) BOOL isRunning;
@property (assign) BOOL isChecking;
@property (assign) NSInteger checkInterval;
@end

@implementation AppDelegate

- (NSAppearance *)lightAppearance {
    return [NSAppearance appearanceNamed:NSAppearanceNameAqua];
}

- (NSString *)syncExecutablePath {
    NSString *resourcePath = [[NSBundle mainBundle] resourcePath];
    NSString *bundled = [resourcePath stringByAppendingPathComponent:@"sync/wecom_sync"];
    if ([[NSFileManager defaultManager] isExecutableFileAtPath:bundled]) return bundled;

    NSString *dev = [[[NSBundle mainBundle] bundlePath] stringByDeletingLastPathComponent];
    dev = [[dev stringByDeletingLastPathComponent] stringByAppendingPathComponent:@"sync/wecom_sync"];
    return dev;
}

- (NSDictionary *)runSyncCommand:(NSArray<NSString *> *)arguments error:(NSString **)errorMessage {
    NSTask *task = [[NSTask alloc] init];
    task.executableURL = [NSURL fileURLWithPath:[self syncExecutablePath]];
    task.arguments = arguments;

    NSMutableDictionary *environment = [[[NSProcessInfo processInfo] environment] mutableCopy];
    environment[@"WECOM_CORPID"] = self.corpID ?: DEFAULT_CORPID;
    environment[@"WECOM_SECRET"] = self.corpSecret ?: DEFAULT_SECRET;
    environment[@"WECOM_CHECK_INTERVAL"] = [NSString stringWithFormat:@"%ld", (long)self.checkInterval];
    task.environment = environment;

    NSPipe *pipe = [NSPipe pipe];
    task.standardOutput = pipe;
    task.standardError = pipe;

    NSError *launchError = nil;
    if (![task launchAndReturnError:&launchError]) {
        if (errorMessage) *errorMessage = launchError.localizedDescription;
        return nil;
    }
    [task waitUntilExit];

    NSData *data = [[pipe fileHandleForReading] readDataToEndOfFile];
    NSString *output = [[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding] ?: @"";
    output = [output stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]];
    NSData *jsonData = [output dataUsingEncoding:NSUTF8StringEncoding];
    NSDictionary *json = jsonData ? [NSJSONSerialization JSONObjectWithData:jsonData options:0 error:nil] : nil;

    if (![json isKindOfClass:[NSDictionary class]]) {
        if (errorMessage) *errorMessage = output.length ? output : @"同步器没有返回有效 JSON";
        return nil;
    }
    return json;
}

- (void)refreshIP {
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        NSString *error = nil;
        NSDictionary *result = [self runSyncCommand:@[@"--ip"] error:&error];
        dispatch_async(dispatch_get_main_queue(), ^{
            NSString *ip = result[@"ip"];
            if (ip.length) {
                self.ipLabel.stringValue = ip;
                [self updateStatus:@"获取到公网 IP，点击「开始监控」自动同步"];
            } else {
                [self updateStatus:[NSString stringWithFormat:@"获取 IP 失败：%@", error ?: @"未知错误"]];
            }
        });
    });
}

- (void)syncOnce {
    if (self.isChecking) return;
    self.isChecking = YES;
    [self updateStatus:@"正在同步并验证企业微信后台页面..."];

    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        NSString *error = nil;
        NSDictionary *result = [self runSyncCommand:@[@"--once"] error:&error];
        dispatch_async(dispatch_get_main_queue(), ^{
            self.isChecking = NO;
            NSString *ip = result[@"ip"];
            if (ip.length) self.ipLabel.stringValue = ip;

            BOOL ok = [result[@"ok"] boolValue];
            BOOL verified = [result[@"verified"] boolValue];
            NSString *message = result[@"message"] ?: error ?: @"未知错误";
            if (ok && verified) {
                [self updateStatus:[NSString stringWithFormat:@"已真实同步并验证：%@", ip ?: @""]];
                self.timeLabel.stringValue = [NSString stringWithFormat:@"上次验证: %@", [self dateString]];
            } else {
                [self updateStatus:[NSString stringWithFormat:@"未验证成功：%@", message]];
                self.timeLabel.stringValue = [NSString stringWithFormat:@"上次尝试: %@", [self dateString]];
            }
        });
    });
}

- (void)startTimer {
    if (self.isRunning) return;
    self.isRunning = YES;
    [self setButton:self.toggleBtn title:@"停止监控" fontSize:14 weight:NSFontWeightSemibold];
    [self syncOnce];
    self.checkTimer = [NSTimer scheduledTimerWithTimeInterval:self.checkInterval target:self selector:@selector(syncOnce) userInfo:nil repeats:YES];
    [[NSRunLoop mainRunLoop] addTimer:self.checkTimer forMode:NSRunLoopCommonModes];
}

- (void)stopTimer {
    self.isRunning = NO;
    [self.checkTimer invalidate];
    self.checkTimer = nil;
    [self setButton:self.toggleBtn title:@"开始监控" fontSize:14 weight:NSFontWeightSemibold];
    [self updateStatus:@"已停止监控"];
}

- (void)toggleTimer {
    self.isRunning ? [self stopTimer] : [self startTimer];
}

- (void)loadConfig {
    NSUserDefaults *defaults = [NSUserDefaults standardUserDefaults];
    self.corpID = [defaults stringForKey:@"cid"] ?: DEFAULT_CORPID;
    self.corpSecret = [defaults stringForKey:@"csec"] ?: DEFAULT_SECRET;
    NSInteger savedInterval = [defaults integerForKey:@"interval"];
    self.checkInterval = savedInterval > 0 ? savedInterval : CHECK_INTERVAL;
}

- (void)saveConfig {
    NSUserDefaults *defaults = [NSUserDefaults standardUserDefaults];
    [defaults setObject:self.corpID forKey:@"cid"];
    [defaults setObject:self.corpSecret forKey:@"csec"];
    [defaults setInteger:self.checkInterval forKey:@"interval"];
}

- (NSString *)dateString {
    NSDateFormatter *formatter = [[NSDateFormatter alloc] init];
    formatter.dateFormat = @"yyyy-MM-dd HH:mm:ss";
    return [formatter stringFromDate:[NSDate date]];
}

- (void)updateStatus:(NSString *)status {
    self.statusLabel.stringValue = status ?: @"";
    self.statusItem.button.toolTip = status;
    NSLog(@"[WeComIP] %@", status);
}

- (void)setupMenuBar {
    self.statusItem = [[NSStatusBar systemStatusBar] statusItemWithLength:NSVariableStatusItemLength];
    self.statusItem.button.toolTip = @"企业微信 IP 同步";
    NSImage *statusIcon = [NSImage imageNamed:@"StatusIconTemplate"];
    if (statusIcon) {
        statusIcon.template = YES;
        statusIcon.size = NSMakeSize(18, 18);
        [self.statusItem.button setImage:statusIcon];
        [self.statusItem.button setImagePosition:NSImageOnly];
    } else {
        self.statusItem.button.title = @"🌐";
    }

    NSMenu *menu = [[NSMenu alloc] init];
    NSMenuItem *show = [[NSMenuItem alloc] initWithTitle:@"显示窗口" action:@selector(showWindow) keyEquivalent:@""];
    show.target = self;
    [menu addItem:show];

    NSMenuItem *sync = [[NSMenuItem alloc] initWithTitle:@"立即同步" action:@selector(syncOnce) keyEquivalent:@"s"];
    sync.target = self;
    [menu addItem:sync];

    [menu addItem:[NSMenuItem separatorItem]];
    [menu addItemWithTitle:@"退出" action:@selector(terminate:) keyEquivalent:@"q"];
    self.statusItem.menu = menu;
}

- (void)showWindow {
    if (self.configView) [self closeConfig];
    [self.window center];
    [self.window makeKeyAndOrderFront:nil];
    [NSApp activateIgnoringOtherApps:YES];
}

- (NSTextField *)labelWithFrame:(NSRect)frame text:(NSString *)text size:(CGFloat)size color:(NSColor *)color alignment:(NSTextAlignment)alignment bold:(BOOL)bold {
    NSTextField *label = [[NSTextField alloc] initWithFrame:frame];
    label.stringValue = text ?: @"";
    label.font = bold ? [NSFont boldSystemFontOfSize:size] : [NSFont systemFontOfSize:size];
    label.alignment = alignment;
    label.bezeled = NO;
    label.editable = NO;
    label.drawsBackground = YES;
    label.backgroundColor = [NSColor whiteColor];
    label.textColor = color ?: [NSColor blackColor];
    return label;
}

- (void)setupWindow {
    self.window = [[NSWindow alloc] initWithContentRect:NSMakeRect(0, 0, 520, 440)
        styleMask:NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable
        backing:NSBackingStoreBuffered defer:NO];
    self.window.title = @"企业微信IP自动同步";
    [self.window setAppearance:[self lightAppearance]];
    self.window.backgroundColor = [NSColor whiteColor];
    self.window.titlebarAppearsTransparent = NO;

    NSView *view = self.window.contentView;
    [view addSubview:[self labelWithFrame:NSMakeRect(0, 405, 520, 28) text:@"企业微信 IP 自动同步" size:18 color:[NSColor blackColor] alignment:NSTextAlignmentCenter bold:YES]];
    [view addSubview:[self labelWithFrame:NSMakeRect(50, 370, 420, 18) text:@"当前公网 IP" size:12 color:[NSColor grayColor] alignment:NSTextAlignmentCenter bold:NO]];

    self.ipLabel = [self labelWithFrame:NSMakeRect(50, 326, 420, 40) text:@"获取中..." size:30 color:[NSColor blackColor] alignment:NSTextAlignmentCenter bold:YES];
    self.ipLabel.font = [NSFont monospacedSystemFontOfSize:30 weight:NSFontWeightBold];
    [view addSubview:self.ipLabel];

    self.timeLabel = [self labelWithFrame:NSMakeRect(50, 296, 420, 18) text:@"尚未验证" size:11 color:[NSColor grayColor] alignment:NSTextAlignmentCenter bold:NO];
    [view addSubview:self.timeLabel];

    self.statusLabel = [self labelWithFrame:NSMakeRect(30, 250, 460, 36) text:@"准备就绪，点击「开始监控」自动同步" size:12 color:[NSColor grayColor] alignment:NSTextAlignmentCenter bold:NO];
    [view addSubview:self.statusLabel];

    self.toggleBtn = [[NSButton alloc] initWithFrame:NSMakeRect(160, 205, 200, 36)];
    [self setButton:self.toggleBtn title:@"开始监控" fontSize:14 weight:NSFontWeightSemibold];
    self.toggleBtn.font = [NSFont systemFontOfSize:14 weight:NSFontWeightSemibold];
    self.toggleBtn.bezelStyle = NSBezelStyleRounded;
    self.toggleBtn.target = self;
    self.toggleBtn.action = @selector(toggleTimer);
    [view addSubview:self.toggleBtn];

    NSButton *syncButton = [[NSButton alloc] initWithFrame:NSMakeRect(30, 207, 110, 30)];
    [self setButton:syncButton title:@"立即同步" fontSize:12 weight:NSFontWeightRegular];
    syncButton.bezelStyle = NSBezelStyleRounded;
    syncButton.target = self;
    syncButton.action = @selector(syncOnce);
    [view addSubview:syncButton];

    NSBox *separator = [[NSBox alloc] initWithFrame:NSMakeRect(30, 188, 460, 1)];
    separator.boxType = NSBoxSeparator;
    [view addSubview:separator];

    NSString *preview = self.corpID.length > 8 ? [self.corpID substringToIndex:8] : self.corpID;
    self.configLabel = [self labelWithFrame:NSMakeRect(30, 158, 320, 18) text:[NSString stringWithFormat:@"CorpID: %@... | %ld秒", preview, (long)self.checkInterval] size:11 color:[NSColor grayColor] alignment:NSTextAlignmentLeft bold:NO];
    [view addSubview:self.configLabel];

    NSButton *editButton = [[NSButton alloc] initWithFrame:NSMakeRect(380, 154, 110, 26)];
    [self setButton:editButton title:@"编辑配置" fontSize:11 weight:NSFontWeightRegular];
    editButton.bezelStyle = NSBezelStyleRounded;
    editButton.target = self;
    editButton.action = @selector(showConfig);
    [view addSubview:editButton];

    [self.window center];
    [self.window makeKeyAndOrderFront:nil];
}

- (NSTextField *)entryWithFrame:(NSRect)frame text:(NSString *)text {
    NSTextField *field = [[NSTextField alloc] initWithFrame:frame];
    field.stringValue = text ?: @"";
    field.font = [NSFont systemFontOfSize:12];
    field.bezeled = YES;
    field.editable = YES;
    field.backgroundColor = [NSColor whiteColor];
    field.textColor = [NSColor blackColor];
    return field;
}

- (void)setButton:(NSButton *)button title:(NSString *)title fontSize:(CGFloat)fontSize weight:(NSFontWeight)weight {
    NSDictionary *attributes = @{
        NSForegroundColorAttributeName: [NSColor blackColor],
        NSFontAttributeName: [NSFont systemFontOfSize:fontSize weight:weight],
    };
    button.attributedTitle = [[NSAttributedString alloc] initWithString:title attributes:attributes];
    button.contentTintColor = [NSColor blackColor];
    [button setAppearance:[self lightAppearance]];
}

- (void)showConfig {
    if (self.configView) { [self closeConfig]; return; }
    NSView *view = self.window.contentView;
    self.configView = [[NSView alloc] initWithFrame:view.bounds];
    self.configView.wantsLayer = YES;
    self.configView.layer.backgroundColor = [[NSColor colorWithCalibratedWhite:0.96 alpha:1] CGColor];

    [self.configView addSubview:[self labelWithFrame:NSMakeRect(30, 396, 440, 24) text:@"配置" size:16 color:[NSColor blackColor] alignment:NSTextAlignmentLeft bold:YES]];
    [self.configView addSubview:[self labelWithFrame:NSMakeRect(30, 352, 100, 22) text:@"CorpID:" size:13 color:[NSColor blackColor] alignment:NSTextAlignmentLeft bold:NO]];
    self.corpIDField = [self entryWithFrame:NSMakeRect(130, 350, 350, 24) text:self.corpID];
    [self.configView addSubview:self.corpIDField];

    [self.configView addSubview:[self labelWithFrame:NSMakeRect(30, 317, 100, 22) text:@"CorpSecret:" size:13 color:[NSColor blackColor] alignment:NSTextAlignmentLeft bold:NO]];
    self.secretField = [self entryWithFrame:NSMakeRect(130, 315, 350, 24) text:self.corpSecret];
    [self.configView addSubview:self.secretField];

    [self.configView addSubview:[self labelWithFrame:NSMakeRect(30, 282, 100, 22) text:@"检测间隔:" size:13 color:[NSColor blackColor] alignment:NSTextAlignmentLeft bold:NO]];
    self.intervalField = [self entryWithFrame:NSMakeRect(130, 280, 90, 24) text:[NSString stringWithFormat:@"%ld", (long)self.checkInterval]];
    [self.configView addSubview:self.intervalField];

    NSButton *saveButton = [[NSButton alloc] initWithFrame:NSMakeRect(130, 220, 100, 30)];
    [self setButton:saveButton title:@"保存" fontSize:12 weight:NSFontWeightRegular];
    saveButton.bezelStyle = NSBezelStyleRounded;
    saveButton.target = self;
    saveButton.action = @selector(saveConfigAction);
    [self.configView addSubview:saveButton];

    NSButton *cancelButton = [[NSButton alloc] initWithFrame:NSMakeRect(245, 220, 100, 30)];
    [self setButton:cancelButton title:@"取消" fontSize:12 weight:NSFontWeightRegular];
    cancelButton.bezelStyle = NSBezelStyleRounded;
    cancelButton.target = self;
    cancelButton.action = @selector(closeConfig);
    [self.configView addSubview:cancelButton];

    [view addSubview:self.configView];
    [self.window makeFirstResponder:self.corpIDField];
}

- (void)saveConfigAction {
    NSCharacterSet *trimSet = [NSCharacterSet whitespaceAndNewlineCharacterSet];
    NSString *corpID = [self.corpIDField.stringValue stringByTrimmingCharactersInSet:trimSet];
    NSString *secret = [self.secretField.stringValue stringByTrimmingCharactersInSet:trimSet];
    NSInteger interval = self.intervalField.stringValue.integerValue;
    if (interval < 60) interval = 60;
    if (!corpID.length || !secret.length) {
        NSAlert *alert = [[NSAlert alloc] init];
        alert.messageText = @"配置不完整";
        alert.informativeText = @"CorpID 和 CorpSecret 不能为空";
        [alert runModal];
        return;
    }
    self.corpID = corpID;
    self.corpSecret = secret;
    self.checkInterval = interval;
    [self saveConfig];

    NSString *preview = corpID.length > 8 ? [corpID substringToIndex:8] : corpID;
    self.configLabel.stringValue = [NSString stringWithFormat:@"CorpID: %@... | %ld秒", preview, (long)interval];
    [self closeConfig];
    [self updateStatus:@"配置已保存"];
    if (self.isRunning) { [self stopTimer]; [self startTimer]; }
}

- (void)closeConfig {
    [self.configView removeFromSuperview];
    self.configView = nil;
}

- (void)applicationDidFinishLaunching:(NSNotification *)note {
    [NSApp setAppearance:[self lightAppearance]];
    [self loadConfig];
    [self setupMenuBar];
    [self setupWindow];
    [self refreshIP];
}

- (BOOL)applicationShouldTerminateAfterLastWindowClosed:(NSApplication *)sender { return NO; }
- (void)applicationWillTerminate:(NSNotification *)note { [self stopTimer]; }

@end

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        NSApplication *app = [NSApplication sharedApplication];
        [app setActivationPolicy:NSApplicationActivationPolicyRegular];
        NSMenu *menubar = [[NSMenu alloc] init];
        NSMenuItem *appMenuItem = [[NSMenuItem alloc] init];
        [menubar addItem:appMenuItem];
        NSMenu *menu = [[NSMenu alloc] init];
        [menu addItemWithTitle:@"退出" action:@selector(terminate:) keyEquivalent:@"q"];
        appMenuItem.submenu = menu;
        app.mainMenu = menubar;
        AppDelegate *delegate = [[AppDelegate alloc] init];
        app.delegate = delegate;
        [app run];
    }
    return 0;
}
