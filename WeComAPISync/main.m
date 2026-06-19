#import <Cocoa/Cocoa.h>

#define DEFAULT_CORPID    @"wwedd915ec24199490"
#define DEFAULT_SECRET    @"tPn9xaosme5iJYF0bfk4Bz-HEfoEMgnx96t32ImWPp0"
#define CHECK_INTERVAL    300

@interface AppDelegate : NSObject <NSApplicationDelegate, NSWindowDelegate>
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
@property (strong) NSButton *saveConfigBtn;
@property (strong) NSStatusItem *statusItem;
@property (strong) NSString *currentIP;
@property (strong) NSString *corpID;
@property (strong) NSString *corpSecret;
@property (strong) NSTimer *checkTimer;
@property (assign) BOOL isRunning;
@property (assign) BOOL isChecking;
@property (assign) NSInteger checkInterval;
@end

@implementation AppDelegate

// MARK: - HTTP
- (void)getJSON:(NSString *)urlStr body:(NSDictionary *)body completion:(void(^)(NSDictionary *json, NSError *err))cb {
    NSMutableURLRequest *req = [NSMutableURLRequest requestWithURL:[NSURL URLWithString:urlStr]];
    req.timeoutInterval = 15;
    if (body) {
        req.HTTPMethod = @"POST";
        req.HTTPBody = [NSJSONSerialization dataWithJSONObject:body options:0 error:nil];
        [req setValue:@"application/json" forHTTPHeaderField:@"Content-Type"];
    }
    [[[NSURLSession sharedSession] dataTaskWithRequest:req completionHandler:^(NSData *d, NSURLResponse *r, NSError *e) {
        if (e) { cb(nil, e); return; }
        cb([NSJSONSerialization JSONObjectWithData:d options:0 error:nil], nil);
    }] resume];
}

// MARK: - 获取公网 IP
- (void)fetchIP:(void(^)(NSString *ip, NSError *err))cb {
    // 尝试多个 IP 源，哪个先返回用哪个
    __block BOOL done = NO;
    void (^trySource)(NSString *) = ^(NSString *urlStr) {
        NSMutableURLRequest *req = [NSMutableURLRequest requestWithURL:[NSURL URLWithString:urlStr]];
        req.timeoutInterval = 8;
        [[[NSURLSession sharedSession] dataTaskWithRequest:req completionHandler:^(NSData *d, NSURLResponse *r, NSError *e) {
            if (done) return;
            if (e) return;
            NSString *text = [[NSString alloc] initWithData:d encoding:NSUTF8StringEncoding];
            text = [text stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]];
            // 尝试从 JSON 中提取 ip
            if ([text hasPrefix:@"{"]) {
                NSData *jd = [text dataUsingEncoding:NSUTF8StringEncoding];
                NSDictionary *json = [NSJSONSerialization JSONObjectWithData:jd options:0 error:nil];
                if (json[@"data"] && [json[@"data"] isKindOfClass:[NSDictionary class]] && json[@"data"][@"ip"]) {
                    text = json[@"data"][@"ip"];
                }
            }
            if (text.length > 0 && ([text containsString:@"."] || [text containsString:@":"])) {
                done = YES;
                cb(text, nil);
            }
        }] resume];
    };
    trySource(@"https://ip.sb/api/ip");
    trySource(@"https://myip.ipip.net/json");
}

// MARK: - 企业微信 API
- (void)syncIP:(NSString *)ip completion:(void(^)(BOOL ok, NSString *msg))cb {
    if (!self.corpID.length || !self.corpSecret.length) { cb(NO, @"CorpID/Secret 未配置"); return; }
    NSString *tokenURL = [NSString stringWithFormat:@"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%@&corpsecret=%@",
                          [self.corpID stringByAddingPercentEncodingWithAllowedCharacters:[NSCharacterSet URLQueryAllowedCharacterSet]],
                          [self.corpSecret stringByAddingPercentEncodingWithAllowedCharacters:[NSCharacterSet URLQueryAllowedCharacterSet]]];
    [self getJSON:tokenURL body:nil completion:^(NSDictionary *j, NSError *e) {
        if (e) { cb(NO, e.localizedDescription); return; }
        if (!j[@"access_token"]) { cb(NO, [NSString stringWithFormat:@"Token err: %@", j[@"errmsg"]]); return; }
        NSString *token = j[@"access_token"];
        // 先试 type=1，不行再试 type=2
        [self tryGetAllowAddr:token type:1 completion:^(NSArray *list, NSString *err) {
            if (err) { cb(NO, err); return; }
            if ([list containsObject:ip]) { cb(YES, [NSString stringWithFormat:@"IP %@ 已在列表中", ip]); return; }
            NSMutableArray *newList = [NSMutableArray arrayWithArray:list];
            [newList addObject:ip];
            [self trySetAllowAddr:token type:1 list:newList completion:^(BOOL ok, NSString *msg) {
                cb(ok, ok ? [NSString stringWithFormat:@"✅ 已添加 %@ (%lu个)", ip, (unsigned long)newList.count] : msg);
            }];
        }];
    }];
}

- (void)tryGetAllowAddr:(NSString *)token type:(int)type completion:(void(^)(NSArray *list, NSString *err))cb {
    NSString *url = [NSString stringWithFormat:@"https://qyapi.weixin.qq.com/cgi-bin/get_allow_address?access_token=%@", token];
    [self getJSON:url body:@{@"type":@(type)} completion:^(NSDictionary *j, NSError *e) {
        if (e) { cb(nil, e.localizedDescription); return; }
        if ([j[@"errcode"] intValue] == 0) { cb(j[@"allow_address"] ?: @[], nil); return; }
        if (type == 1) { [self tryGetAllowAddr:token type:2 completion:cb]; return; }
        cb(nil, [NSString stringWithFormat:@"获取失败: %@", j[@"errmsg"]]);
    }];
}

- (void)trySetAllowAddr:(NSString *)token type:(int)type list:(NSArray *)list completion:(void(^)(BOOL ok, NSString *msg))cb {
    NSString *url = [NSString stringWithFormat:@"https://qyapi.weixin.qq.com/cgi-bin/set_allow_address?access_token=%@", token];
    [self getJSON:url body:@{@"type":@(type), @"address_list":list} completion:^(NSDictionary *j, NSError *e) {
        if (e) { cb(NO, e.localizedDescription); return; }
        if ([j[@"errcode"] intValue] == 0) { cb(YES, nil); return; }
        if (type == 1) { [self trySetAllowAddr:token type:2 list:list completion:cb]; return; }
        cb(NO, [NSString stringWithFormat:@"设置失败: %@", j[@"errmsg"]]);
    }];
}

// MARK: - 定时同步
- (void)doSync {
    if (self.isChecking) return;
    self.isChecking = YES;
    [self updateStatus:@"正在检测公网 IP..."];
    [self fetchIP:^(NSString *ip, NSError *err) {
        if (err) {
            dispatch_async(dispatch_get_main_queue(), ^{
                [self updateStatus:[NSString stringWithFormat:@"❌ 获取 IP 失败: %@", err.localizedDescription]];
                self.isChecking = NO;
            });
            return;
        }
        self.currentIP = ip;
        dispatch_async(dispatch_get_main_queue(), ^{
            self.ipLabel.stringValue = ip ?: @"未知";
            [self updateStatus:[NSString stringWithFormat:@"正在同步 %@ 到企业微信...", ip]];
        });
        [self syncIP:ip completion:^(BOOL ok, NSString *msg) {
            dispatch_async(dispatch_get_main_queue(), ^{
                [self updateStatus:ok ? [NSString stringWithFormat:@"✅ %@", msg] : [NSString stringWithFormat:@"❌ %@", msg]];
                self.timeLabel.stringValue = [NSString stringWithFormat:@"上次同步: %@", [self.dateStr stringFromDate:[NSDate date]]];
                self.isChecking = NO;
            });
        }];
    }];
}

- (void)startTimer {
    if (self.isRunning) return;
    self.isRunning = YES;
    [self doSync];
    self.checkTimer = [NSTimer scheduledTimerWithTimeInterval:self.checkInterval target:self selector:@selector(doSync) userInfo:nil repeats:YES];
    [[NSRunLoop mainRunLoop] addTimer:self.checkTimer forMode:NSRunLoopCommonModes];
    dispatch_async(dispatch_get_main_queue(), ^{ self.toggleBtn.title = @"⏹ 停止监控"; });
}

- (void)stopTimer {
    self.isRunning = NO;
    [self.checkTimer invalidate]; self.checkTimer = nil;
    dispatch_async(dispatch_get_main_queue(), ^{ self.toggleBtn.title = @"▶ 开始监控"; });
}

- (void)toggleTimer {
    self.isRunning ? [self stopTimer] : [self startTimer];
}

// MARK: - 配置
- (void)loadConfig {
    NSUserDefaults *def = [NSUserDefaults standardUserDefaults];
    self.corpID = [def stringForKey:@"cid"] ?: DEFAULT_CORPID;
    self.corpSecret = [def stringForKey:@"csec"] ?: DEFAULT_SECRET;
    self.checkInterval = [def integerForKey:@"interval"] > 0 ? [def integerForKey:@"interval"] : CHECK_INTERVAL;
}

- (void)saveConfig {
    NSUserDefaults *def = [NSUserDefaults standardUserDefaults];
    [def setObject:self.corpID forKey:@"cid"];
    [def setObject:self.corpSecret forKey:@"csec"];
    [def setInteger:self.checkInterval forKey:@"interval"];
}

// MARK: - 辅助
- (NSDateFormatter *)dateStr {
    NSDateFormatter *f = [[NSDateFormatter alloc] init];
    f.dateFormat = @"yyyy-MM-dd HH:mm:ss";
    return f;
}

- (void)updateStatus:(NSString *)s {
    self.statusLabel.stringValue = s;
    self.statusItem.button.toolTip = s;
    NSLog(@"[WeComIP] %@", s);
}

// MARK: - 菜单栏
- (void)setupMenuBar {
    self.statusItem = [[NSStatusBar systemStatusBar] statusItemWithLength:NSVariableStatusItemLength];
    self.statusItem.button.title = @"🌐";
    self.statusItem.button.toolTip = @"企业微信 IP 同步";
    NSMenu *menu = [[NSMenu alloc] init];
    NSMenuItem *show = [[NSMenuItem alloc] initWithTitle:@"显示窗口" action:@selector(showWin) keyEquivalent:@""];
    show.target = self; [menu addItem:show];
    [menu addItem:[NSMenuItem separatorItem]];
    NSMenuItem *sync = [[NSMenuItem alloc] initWithTitle:@"立即同步" action:@selector(doSync) keyEquivalent:@"s"];
    sync.target = self; [menu addItem:sync];
    [menu addItem:[NSMenuItem separatorItem]];
    [menu addItemWithTitle:@"退出" action:@selector(terminate:) keyEquivalent:@"q"];
    self.statusItem.menu = menu;
}

- (void)showWin {
    if (self.configView) { [self.configView removeFromSuperview]; self.configView = nil; }
    if (!self.window) {
        [self setupWindow];
        return;
    }
    [self.window center];
    [self.window makeKeyAndOrderFront:nil];
    [NSApp activateIgnoringOtherApps:YES];
}

// MARK: - 主窗口
- (void)setupWindow {
    self.window = [[NSWindow alloc] initWithContentRect:NSMakeRect(0,0,500,440)
        styleMask:NSWindowStyleMaskTitled|NSWindowStyleMaskClosable|NSWindowStyleMaskMiniaturizable
        backing:NSBackingStoreBuffered defer:NO];
    self.window.title = @"企业微信IP自动同步";
    self.window.backgroundColor = [NSColor whiteColor];

    NSView *v = self.window.contentView;

    // Title
    NSTextField *title = [[NSTextField alloc] initWithFrame:NSMakeRect(0, 410, 500, 26)];
    title.stringValue = @"📡 企业微信 IP 自动同步";
    title.font = [NSFont boldSystemFontOfSize:17]; title.alignment = NSTextAlignmentCenter;
    title.bezeled = NO; title.editable = NO; title.drawsBackground = YES; title.backgroundColor = [NSColor whiteColor]; title.textColor = [NSColor blackColor];
    [v addSubview:title];

    // IP
    NSTextField *hdr = [[NSTextField alloc] initWithFrame:NSMakeRect(50, 375, 400, 16)];
    hdr.stringValue = @"当前公网 IP"; hdr.font = [NSFont systemFontOfSize:12]; hdr.alignment = NSTextAlignmentCenter;
    hdr.bezeled = NO; hdr.editable = NO; hdr.drawsBackground = YES; hdr.backgroundColor = [NSColor whiteColor]; hdr.textColor = [NSColor grayColor];
    [v addSubview:hdr];

    self.ipLabel = [[NSTextField alloc] initWithFrame:NSMakeRect(50, 335, 400, 36)];
    self.ipLabel.stringValue = @"获取中...";
    self.ipLabel.font = [NSFont monospacedSystemFontOfSize:28 weight:NSFontWeightBold];
    self.ipLabel.alignment = NSTextAlignmentCenter; self.ipLabel.bezeled = NO; self.ipLabel.editable = NO;
    self.ipLabel.drawsBackground = YES; self.ipLabel.backgroundColor = [NSColor whiteColor]; self.ipLabel.textColor = [NSColor blackColor];
    [v addSubview:self.ipLabel];

    // Time
    self.timeLabel = [[NSTextField alloc] initWithFrame:NSMakeRect(50, 305, 400, 16)];
    self.timeLabel.stringValue = @"尚未同步"; self.timeLabel.font = [NSFont systemFontOfSize:11];
    self.timeLabel.alignment = NSTextAlignmentCenter; self.timeLabel.bezeled = NO; self.timeLabel.editable = NO;
    self.timeLabel.drawsBackground = YES; self.timeLabel.backgroundColor = [NSColor whiteColor]; self.timeLabel.textColor = [NSColor grayColor];
    [v addSubview:self.timeLabel];

    // Status
    self.statusLabel = [[NSTextField alloc] initWithFrame:NSMakeRect(30, 265, 440, 30)];
    self.statusLabel.stringValue = @"准备就绪，点击「开始监控」自动同步";
    self.statusLabel.font = [NSFont systemFontOfSize:12]; self.statusLabel.alignment = NSTextAlignmentCenter;
    self.statusLabel.bezeled = NO; self.statusLabel.editable = NO; self.statusLabel.drawsBackground = YES; self.statusLabel.backgroundColor = [NSColor whiteColor];
    self.statusLabel.textColor = [NSColor grayColor];
    [v addSubview:self.statusLabel];

    // Button
    self.toggleBtn = [[NSButton alloc] initWithFrame:NSMakeRect(150, 218, 200, 36)];
    self.toggleBtn.title = @"▶ 开始监控";
    self.toggleBtn.font = [NSFont systemFontOfSize:14 weight:NSFontWeightSemibold];
    self.toggleBtn.bezelStyle = NSBezelStyleRounded;
    self.toggleBtn.target = self; self.toggleBtn.action = @selector(toggleTimer);
    [v addSubview:self.toggleBtn];

    // Separator
    NSBox *sep = [[NSBox alloc] initWithFrame:NSMakeRect(30, 200, 440, 1)]; sep.boxType = NSBoxSeparator; [v addSubview:sep];

    // Config label
    NSString *preview = self.corpID.length > 8 ? [self.corpID substringToIndex:8] : self.corpID;
    self.configLabel = [[NSTextField alloc] initWithFrame:NSMakeRect(30, 170, 300, 18)];
    self.configLabel.stringValue = [NSString stringWithFormat:@"⚙️ CorpID: %@... | %ld秒", preview, (long)self.checkInterval];
    self.configLabel.font = [NSFont systemFontOfSize:11]; self.configLabel.bezeled = NO; self.configLabel.editable = NO;
    self.configLabel.drawsBackground = YES; self.configLabel.backgroundColor = [NSColor whiteColor]; self.configLabel.textColor = [NSColor grayColor];
    [v addSubview:self.configLabel];

    // Edit button
    NSButton *editBtn = [[NSButton alloc] initWithFrame:NSMakeRect(370, 167, 110, 24)];
    editBtn.title = @"✏️ 编辑配置"; editBtn.font = [NSFont systemFontOfSize:11];
    editBtn.bezelStyle = NSBezelStyleRounded; editBtn.target = self; editBtn.action = @selector(showConfig);
    [v addSubview:editBtn];

    [self.window center];
    [self.window makeKeyAndOrderFront:nil];
}

// MARK: - 配置面板
- (void)showConfig {
    if (self.configView) { [self closeConfig]; return; }
    NSView *v = self.window.contentView;
    CGFloat h = v.bounds.size.height;
    self.configView = [[NSView alloc] initWithFrame:v.bounds];
    self.configView.wantsLayer = YES;
    self.configView.layer.backgroundColor = [[NSColor colorWithCalibratedWhite:0.96 alpha:1] CGColor];

    NSTextField *ct = [[NSTextField alloc] initWithFrame:NSMakeRect(30, h-40, 440, 24)];
    ct.stringValue = @"⚙️ 配置"; ct.font = [NSFont boldSystemFontOfSize:16];
    ct.bezeled = NO; ct.editable = NO; ct.drawsBackground = YES; ct.backgroundColor = [NSColor whiteColor]; ct.textColor = [NSColor blackColor];
    [self.configView addSubview:ct];

    CGFloat row = h - 80;
    NSTextField *cl = [[NSTextField alloc] initWithFrame:NSMakeRect(30, row, 100, 22)];
    cl.stringValue = @"CorpID:"; cl.font = [NSFont systemFontOfSize:13];
    cl.bezeled = NO; cl.editable = NO; cl.drawsBackground = YES; cl.backgroundColor = [NSColor whiteColor]; cl.textColor = [NSColor blackColor];
    [self.configView addSubview:cl];

    self.corpIDField = [[NSTextField alloc] initWithFrame:NSMakeRect(130, row-2, 340, 24)];
    self.corpIDField.stringValue = self.corpID; self.corpIDField.font = [NSFont systemFontOfSize:12];
    self.corpIDField.bezeled = YES; self.corpIDField.editable = YES;
    self.corpIDField.backgroundColor = [NSColor whiteColor]; self.corpIDField.textColor = [NSColor blackColor];
    [self.configView addSubview:self.corpIDField];

    row = h - 115;
    NSTextField *sl = [[NSTextField alloc] initWithFrame:NSMakeRect(30, row, 100, 22)];
    sl.stringValue = @"CorpSecret:"; sl.font = [NSFont systemFontOfSize:13];
    sl.bezeled = NO; sl.editable = NO; sl.drawsBackground = YES; sl.backgroundColor = [NSColor whiteColor]; sl.textColor = [NSColor blackColor];
    [self.configView addSubview:sl];

    self.secretField = [[NSTextField alloc] initWithFrame:NSMakeRect(130, row-2, 340, 24)];
    self.secretField.stringValue = self.corpSecret; self.secretField.font = [NSFont systemFontOfSize:11];
    self.secretField.bezeled = YES; self.secretField.editable = YES;
    self.secretField.backgroundColor = [NSColor whiteColor]; self.secretField.textColor = [NSColor blackColor];
    [self.configView addSubview:self.secretField];

    row = h - 150;
    NSTextField *il = [[NSTextField alloc] initWithFrame:NSMakeRect(30, row, 100, 22)];
    il.stringValue = @"检测间隔(秒):"; il.font = [NSFont systemFontOfSize:13];
    il.bezeled = NO; il.editable = NO; il.drawsBackground = YES; il.backgroundColor = [NSColor whiteColor]; il.textColor = [NSColor blackColor];
    [self.configView addSubview:il];

    self.intervalField = [[NSTextField alloc] initWithFrame:NSMakeRect(130, row-2, 80, 24)];
    self.intervalField.stringValue = [NSString stringWithFormat:@"%ld", (long)self.checkInterval];
    self.intervalField.font = [NSFont systemFontOfSize:12]; self.intervalField.bezeled = YES; self.intervalField.editable = YES;
    self.intervalField.backgroundColor = [NSColor whiteColor]; self.intervalField.textColor = [NSColor blackColor];
    [self.configView addSubview:self.intervalField];

    row = h - 210;
    self.saveConfigBtn = [[NSButton alloc] initWithFrame:NSMakeRect(130, row, 100, 28)];
    self.saveConfigBtn.title = @"保存"; self.saveConfigBtn.font = [NSFont systemFontOfSize:13 weight:NSFontWeightSemibold];
    self.saveConfigBtn.bezelStyle = NSBezelStyleRounded; self.saveConfigBtn.target = self; self.saveConfigBtn.action = @selector(saveConfigAction);
    [self.configView addSubview:self.saveConfigBtn];

    NSButton *cancelBtn = [[NSButton alloc] initWithFrame:NSMakeRect(240, row, 100, 28)];
    cancelBtn.title = @"取消"; cancelBtn.font = [NSFont systemFontOfSize:12];
    cancelBtn.bezelStyle = NSBezelStyleRounded; cancelBtn.target = self; cancelBtn.action = @selector(closeConfig);
    [self.configView addSubview:cancelBtn];

    [v addSubview:self.configView];
    [self.window makeFirstResponder:self.corpIDField];
}

- (void)saveConfigAction {
    NSString *cid = self.corpIDField.stringValue;
    NSString *sec = self.secretField.stringValue;
    NSInteger iv = [self.intervalField.stringValue integerValue];
    if (iv < 60) iv = 60; if (iv > 86400) iv = 86400;
    if (!cid.length || !sec.length) {
        NSAlert *a = [[NSAlert alloc] init]; a.messageText = @"配置不完整"; a.informativeText = @"CorpID 和 CorpSecret 不能为空"; [a runModal];
        return;
    }
    self.corpID = cid; self.corpSecret = sec; self.checkInterval = iv;
    [self saveConfig];
    NSString *preview = cid.length > 8 ? [cid substringToIndex:8] : cid;
    self.configLabel.stringValue = [NSString stringWithFormat:@"⚙️ CorpID: %@... | %ld秒", preview, (long)iv];
    [self closeConfig];
    [self updateStatus:@"✅ 配置已保存"];
    if (self.isRunning) { [self stopTimer]; [self startTimer]; [self updateStatus:@"✅ 配置已保存，监控已重启"]; }
}

- (void)closeConfig { [self.configView removeFromSuperview]; self.configView = nil; }

// MARK: - NSApplicationDelegate
- (void)applicationDidFinishLaunching:(NSNotification *)note {
    @try {
    [self loadConfig];
    [self setupMenuBar];
    [self setupWindow];
    [self fetchIP:^(NSString *ip, NSError *err) {
        dispatch_async(dispatch_get_main_queue(), ^{
            if (ip) { self.currentIP = ip; self.ipLabel.stringValue = ip; }
            if (!self.isRunning) [self updateStatus:@"获取到公网 IP，点击「开始监控」自动同步"];
        });
    }];
    } @catch (NSException *e) {
        NSLog(@"[CRASH] %@", e);
    }
}

- (BOOL)applicationShouldTerminateAfterLastWindowClosed:(NSApplication *)sender { return NO; }
- (void)applicationWillTerminate:(NSNotification *)note { [self stopTimer]; }

// 关闭窗口时只隐藏不退出
- (BOOL)windowShouldClose:(NSWindow *)sender {
    [self.window orderOut:self];
    return NO;
}

@end

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        NSApplication *app = [NSApplication sharedApplication];
        [app setActivationPolicy:NSApplicationActivationPolicyRegular];
        NSMenu *mb = [[NSMenu alloc] init];
        NSMenuItem *ai = [[NSMenuItem alloc] init]; [mb addItem:ai];
        NSMenu *m = [[NSMenu alloc] init]; [m addItemWithTitle:@"退出" action:@selector(terminate:) keyEquivalent:@"q"]; ai.submenu = m;
        app.mainMenu = mb;
        AppDelegate *d = [[AppDelegate alloc] init];
        app.delegate = d;
        [app run];
    }
    return 0;
}
