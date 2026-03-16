using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;
using System.Windows.Automation;
using Microsoft.Win32;
using Telos.UIGraph.Windows.Models;

namespace Telos.UIGraph.Windows.Services;

/// <summary>
/// Windows UI Automation extraction service.
/// Walks the UIA tree of target application windows and produces structured snapshots.
/// All password fields are detected and masked.
/// </summary>
public sealed class UIAutomationService
{
    private const int MaxDepth = 8;
    private const int MaxChildren = 100;
    private const string PasswordMask = "***MASKED***";

    /// <summary>
    /// Find and snapshot a window by partial process/title match.
    /// </summary>
    public UISnapshotDto? CaptureSnapshot(string appName)
    {
        if (string.IsNullOrWhiteSpace(appName))
            return null;

        var rootElement = AutomationElement.RootElement;
        var appNameLower = appName.ToLowerInvariant();

        // Search all top-level windows
        var windows = rootElement.FindAll(
            TreeScope.Children,
            new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Window)
        );

        foreach (AutomationElement window in windows)
        {
            try
            {
                var name = window.Current.Name?.ToLowerInvariant() ?? "";
                var processName = "";
                int processId = 0;

                try
                {
                    processId = window.Current.ProcessId;
                    var proc = Process.GetProcessById(processId);
                    processName = proc.ProcessName.ToLowerInvariant();
                }
                catch { }

                if (name.Contains(appNameLower) || processName.Contains(appNameLower))
                {
                    var snapshot = new UISnapshotDto
                    {
                        WindowTitle = window.Current.Name ?? "",
                        ProcessName = processName,
                        ProcessId = processId,
                        Timestamp = DateTime.UtcNow.ToString("o"),
                        Elements = ExtractChildren(window, 0),
                    };
                    return snapshot;
                }
            }
            catch (ElementNotAvailableException) { continue; }
        }

        return null;
    }

    /// <summary>
    /// List all visible application windows.
    /// </summary>
    public List<UISnapshotDto> ListWindows()
    {
        var result = new List<UISnapshotDto>();
        var rootElement = AutomationElement.RootElement;

        var windows = rootElement.FindAll(
            TreeScope.Children,
            new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Window)
        );

        foreach (AutomationElement window in windows)
        {
            try
            {
                var processId = window.Current.ProcessId;
                var processName = "";
                try
                {
                    var proc = Process.GetProcessById(processId);
                    processName = proc.ProcessName;
                }
                catch { }

                result.Add(new UISnapshotDto
                {
                    WindowTitle = window.Current.Name ?? "",
                    ProcessName = processName,
                    ProcessId = processId,
                    Timestamp = DateTime.UtcNow.ToString("o"),
                });
            }
            catch (ElementNotAvailableException) { continue; }
        }

        return result;
    }

    /// <summary>
    /// Focus a window by app name (bring to foreground).
    /// </summary>
    public bool FocusWindow(string appName)
    {
        var snapshot = CaptureSnapshot(appName);
        if (snapshot == null)
        {
            try
            {
                // Try to launch the app if it's not found (e.g. "notepad")
                Process.Start(new ProcessStartInfo { FileName = appName, UseShellExecute = true });
                System.Threading.Thread.Sleep(1500); // Give it a moment to initialize
                snapshot = CaptureSnapshot(appName);
            }
            catch { }
        }

        if (snapshot == null) return false;

        try
        {
            var proc = Process.GetProcessById(snapshot.ProcessId);
            var hwnd = proc.MainWindowHandle;
            if (hwnd != IntPtr.Zero)
            {
                SetForegroundWindow(hwnd);
                return true;
            }
        }
        catch { }

        return false;
    }

    /// <summary>
    /// Write a value to a target UI element by name/automation ID match.
    /// </summary>
    public bool WriteValue(string appName, string target, string value)
    {
        if (string.IsNullOrWhiteSpace(appName) || string.IsNullOrWhiteSpace(target))
            return false;

        var rootElement = AutomationElement.RootElement;
        var appNameLower = appName.ToLowerInvariant();
        var targetLower = target.ToLowerInvariant();

        var windows = rootElement.FindAll(
            TreeScope.Children,
            new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Window)
        );

        foreach (AutomationElement window in windows)
        {
            try
            {
                var name = window.Current.Name?.ToLowerInvariant() ?? "";
                var processName = "";
                try
                {
                    var proc = Process.GetProcessById(window.Current.ProcessId);
                    processName = proc.ProcessName.ToLowerInvariant();
                }
                catch { }

                if (!name.Contains(appNameLower) && !processName.Contains(appNameLower))
                    continue;

                // Find target element
                var element = FindElementByDescription(window, targetLower);
                if (element == null) continue;

                // Try ValuePattern
                if (element.TryGetCurrentPattern(ValuePattern.Pattern, out object? valPattern))
                {
                    var vp = (ValuePattern)valPattern;
                    if (!vp.Current.IsReadOnly)
                    {
                        vp.SetValue(value);
                        return true;
                    }
                }

                // Try keyboard input as fallback
                element.SetFocus();
                System.Windows.Forms.SendKeys.SendWait("^a"); // Select all
                System.Windows.Forms.SendKeys.SendWait(EscapeSendKeys(value));
                return true;
            }
            catch (ElementNotAvailableException) { continue; }
            catch (Exception) { continue; }
        }

        return false;
    }

    private List<UIElementDto> ExtractChildren(AutomationElement parent, int depth)
    {
        var result = new List<UIElementDto>();
        if (depth >= MaxDepth) return result;

        AutomationElementCollection children;
        try
        {
            children = parent.FindAll(TreeScope.Children, Condition.TrueCondition);
        }
        catch { return result; }

        int count = 0;
        foreach (AutomationElement child in children)
        {
            if (count++ >= MaxChildren) break;

            try
            {
                var element = ExtractElement(child, depth);
                result.Add(element);
            }
            catch (ElementNotAvailableException) { continue; }
        }

        return result;
    }

    private UIElementDto ExtractElement(AutomationElement el, int depth)
    {
        var current = el.Current;
        bool isPassword = false;
        string value = "";

        // Check if this is a password field
        try
        {
            if (current.ControlType == ControlType.Edit)
            {
                if (el.TryGetCurrentPattern(ValuePattern.Pattern, out object? vp))
                {
                    var valuePattern = (ValuePattern)vp;
                    // If the control is a password box, mask it
                    isPassword = current.ClassName?.Contains("Password") == true
                              || current.AutomationId?.ToLowerInvariant().Contains("password") == true
                              || current.Name?.ToLowerInvariant().Contains("password") == true;

                    value = isPassword ? PasswordMask : valuePattern.Current.Value ?? "";
                }
            }
            else
            {
                if (el.TryGetCurrentPattern(ValuePattern.Pattern, out object? vp))
                {
                    value = ((ValuePattern)vp).Current.Value ?? "";
                }
            }
        }
        catch { }

        var rect = current.BoundingRectangle;

        return new UIElementDto
        {
            AutomationId = current.AutomationId ?? "",
            Name = current.Name ?? "",
            ControlType = current.ControlType?.ProgrammaticName?.Replace("ControlType.", "") ?? "",
            Value = value,
            BoundingRect = new Dictionary<string, int>
            {
                ["x"] = (int)rect.X,
                ["y"] = (int)rect.Y,
                ["width"] = (int)rect.Width,
                ["height"] = (int)rect.Height,
            },
            Children = ExtractChildren(el, depth + 1),
            IsPassword = isPassword,
        };
    }

    private AutomationElement? FindElementByDescription(AutomationElement root, string targetLower)
    {
        // Search by Name or AutomationId
        try
        {
            var all = root.FindAll(TreeScope.Descendants, Condition.TrueCondition);
            foreach (AutomationElement el in all)
            {
                try
                {
                    var elName = el.Current.Name?.ToLowerInvariant() ?? "";
                    var elId = el.Current.AutomationId?.ToLowerInvariant() ?? "";

                    // Match cell references like "B4" for spreadsheets
                    if (elName.Contains(targetLower) || elId.Contains(targetLower))
                        return el;

                    // Partial keyword match
                    var keywords = targetLower.Split(' ', StringSplitOptions.RemoveEmptyEntries);
                    if (keywords.Length > 1 && keywords.All(kw => elName.Contains(kw) || elId.Contains(kw)))
                        return el;
                }
                catch (ElementNotAvailableException) { continue; }
            }
        }
        catch { }

        return null;
    }

    private static string EscapeSendKeys(string text)
    {
        // Escape special SendKeys characters
        return text
            .Replace("+", "{+}")
            .Replace("^", "{^}")
            .Replace("%", "{%}")
            .Replace("~", "{~}")
            .Replace("(", "{(}")
            .Replace(")", "{)}")
            .Replace("{", "{{}}")
            .Replace("}", "{}}");
    }

    // ── Application Launch ───────────────────────────────────────────────

    private static readonly Regex _safeForShell =
        new(@"^[\w\s\.\-\(\)]+$", RegexOptions.Compiled);

    /// <summary>
    /// Launch an application by friendly name.
    /// Resolution order: hint_exe → registry App Paths → Start Menu shortcuts
    /// → UWP/Store via Get-AppxPackage → ShellExecute fallback.
    /// </summary>
    public async Task<LaunchResult> LaunchApplication(string appName, string? hintExe = null)
    {
        if (string.IsNullOrWhiteSpace(appName))
            return new LaunchResult { Message = "app_name is required" };

        // 1. Already running? Just focus it.
        var existing = CaptureSnapshot(appName);
        if (existing != null)
        {
            FocusWindow(appName);
            return new LaunchResult { Success = true, AlreadyRunning = true, LaunchMethod = "focus_existing" };
        }

        // 2. Caller provided a direct exe path.
        if (!string.IsNullOrEmpty(hintExe) && File.Exists(hintExe))
        {
            if (TryShellExecute(hintExe))
            {
                await Task.Delay(2500);
                return new LaunchResult
                {
                    Success = CaptureSnapshot(appName) != null,
                    LaunchMethod = "hint_exe",
                };
            }
        }

        // 3. Registry App Paths: HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths
        var regExe = LookupRegistryAppPaths(appName);
        if (regExe != null && TryShellExecute(regExe))
        {
            await Task.Delay(2500);
            return new LaunchResult
            {
                Success = CaptureSnapshot(appName) != null,
                LaunchMethod = "registry",
            };
        }

        // 4. Start Menu .lnk shortcut
        var lnk = FindStartMenuShortcut(appName);
        if (lnk != null && TryShellExecute(lnk))
        {
            await Task.Delay(2500);
            return new LaunchResult
            {
                Success = CaptureSnapshot(appName) != null,
                LaunchMethod = "start_menu",
            };
        }

        // 5. UWP / Microsoft Store — shell:AppsFolder\PFN!App
        var uwpId = await FindUwpAppId(appName);
        if (uwpId != null && TryShellExecute($"shell:AppsFolder\\{uwpId}"))
        {
            await Task.Delay(3500);
            return new LaunchResult
            {
                Success = CaptureSnapshot(appName) != null,
                LaunchMethod = "uwp_store",
            };
        }

        // 6. ShellExecute fallback — works for PATH-resolved names like "notepad"
        if (TryShellExecute(appName))
        {
            await Task.Delay(1500);
            return new LaunchResult
            {
                Success = CaptureSnapshot(appName) != null,
                LaunchMethod = "shell_fallback",
            };
        }

        return new LaunchResult { Message = $"Could not find or launch: {appName}" };
    }

    private static bool TryShellExecute(string target)
    {
        try
        {
            Process.Start(new ProcessStartInfo { FileName = target, UseShellExecute = true });
            return true;
        }
        catch { return false; }
    }

    private static string? LookupRegistryAppPaths(string appName)
    {
        foreach (var candidate in new[] { appName, appName + ".exe" })
        {
            var key = candidate.EndsWith(".exe", StringComparison.OrdinalIgnoreCase)
                ? candidate : candidate + ".exe";
            try
            {
                using var reg = Registry.LocalMachine.OpenSubKey(
                    $@"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{key}", writable: false);
                if (reg?.GetValue(null) is string path && File.Exists(path))
                    return path;
            }
            catch { }
        }
        return null;
    }

    private static string? FindStartMenuShortcut(string appName)
    {
        var roots = new[]
        {
            Environment.GetFolderPath(Environment.SpecialFolder.StartMenu),
            Environment.GetFolderPath(Environment.SpecialFolder.CommonStartMenu),
        };
        var nameLower = appName.ToLowerInvariant();
        foreach (var root in roots.Where(Directory.Exists))
        {
            try
            {
                foreach (var lnk in Directory.EnumerateFiles(root, "*.lnk", SearchOption.AllDirectories))
                {
                    var stem = Path.GetFileNameWithoutExtension(lnk).ToLowerInvariant();
                    if (stem.Contains(nameLower) || nameLower.Contains(stem))
                        return lnk;
                }
            }
            catch { }
        }
        return null;
    }

    private static async Task<string?> FindUwpAppId(string appName)
    {
        // Strip any non-safe chars to prevent PowerShell injection
        var safe = Regex.Replace(appName, @"[^\w\s\.\-]", "").Trim();
        if (string.IsNullOrWhiteSpace(safe)) return null;

        try
        {
            using var proc = new Process
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = "powershell.exe",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    CreateNoWindow = true,
                }
            };
            proc.StartInfo.ArgumentList.Add("-NoProfile");
            proc.StartInfo.ArgumentList.Add("-NonInteractive");
            proc.StartInfo.ArgumentList.Add("-Command");
            proc.StartInfo.ArgumentList.Add(
                $"Get-AppxPackage -Name '*{safe}*' | Select-Object -First 1 -ExpandProperty PackageFamilyName"
            );
            proc.Start();
            var output = await proc.StandardOutput.ReadToEndAsync();
            await Task.Run(() => proc.WaitForExit(5000));
            var pfn = output.Trim();
            // Sanity-check: single line, no path separators injected
            if (!string.IsNullOrEmpty(pfn) && !pfn.Contains('\n') && pfn.Length < 200)
                return $"{pfn}!App";
        }
        catch { }
        return null;
    }

    // ── Advanced UIA Control Patterns ────────────────────────────────────

    /// <summary>Finds the first top-level window matching the app name (case-insensitive).</summary>
    private AutomationElement? FindWindowForApp(string appNameLower)
    {
        var windows = AutomationElement.RootElement.FindAll(
            TreeScope.Children,
            new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Window));
        foreach (AutomationElement win in windows)
        {
            try
            {
                var title = win.Current.Name?.ToLowerInvariant() ?? "";
                var proc = "";
                try { proc = Process.GetProcessById(win.Current.ProcessId).ProcessName.ToLowerInvariant(); } catch { }
                if (title.Contains(appNameLower) || proc.Contains(appNameLower))
                    return win;
            }
            catch (ElementNotAvailableException) { continue; }
        }
        return null;
    }

    /// <summary>Invoke (click) a button or interactive element via InvokePattern.</summary>
    public bool InvokeElement(string appName, string target)
    {
        var win = FindWindowForApp(appName.ToLowerInvariant());
        if (win == null) return false;
        var el = FindElementByDescription(win, target.ToLowerInvariant());
        if (el == null) return false;
        try
        {
            if (el.TryGetCurrentPattern(InvokePattern.Pattern, out var p))
            {
                ((InvokePattern)p).Invoke();
                return true;
            }
        }
        catch { }
        // Fallback: focus and press Space
        try { el.SetFocus(); System.Windows.Forms.SendKeys.SendWait(" "); return true; }
        catch { return false; }
    }

    /// <summary>Expand or collapse a dropdown/tree/menu element.</summary>
    public bool ExpandCollapseElement(string appName, string target)
    {
        var win = FindWindowForApp(appName.ToLowerInvariant());
        if (win == null) return false;
        var el = FindElementByDescription(win, target.ToLowerInvariant());
        if (el == null) return false;
        try
        {
            if (el.TryGetCurrentPattern(ExpandCollapsePattern.Pattern, out var p))
            {
                var ecp = (ExpandCollapsePattern)p;
                if (ecp.Current.ExpandCollapseState == ExpandCollapseState.Collapsed)
                    ecp.Expand();
                else
                    ecp.Collapse();
                return true;
            }
        }
        catch { }
        return false;
    }

    /// <summary>Select an item in a list, combo box, or radio group.</summary>
    public bool SelectItem(string appName, string target)
    {
        var win = FindWindowForApp(appName.ToLowerInvariant());
        if (win == null) return false;
        var el = FindElementByDescription(win, target.ToLowerInvariant());
        if (el == null) return false;
        try
        {
            if (el.TryGetCurrentPattern(SelectionItemPattern.Pattern, out var p))
            {
                ((SelectionItemPattern)p).Select();
                return true;
            }
        }
        catch { }
        return false;
    }

    /// <summary>Toggle a checkbox or other toggle-able element.</summary>
    public bool ToggleElement(string appName, string target)
    {
        var win = FindWindowForApp(appName.ToLowerInvariant());
        if (win == null) return false;
        var el = FindElementByDescription(win, target.ToLowerInvariant());
        if (el == null) return false;
        try
        {
            if (el.TryGetCurrentPattern(TogglePattern.Pattern, out var p))
            {
                ((TogglePattern)p).Toggle();
                return true;
            }
        }
        catch { }
        return false;
    }

    /// <summary>
    /// Read text from the target element (or entire window).
    /// Uses TextPattern first; falls back to aggregating ValuePattern values.
    /// </summary>
    public string? ReadText(string appName, string? target = null)
    {
        var win = FindWindowForApp(appName.ToLowerInvariant());
        if (win == null) return null;

        if (!string.IsNullOrWhiteSpace(target))
        {
            var el = FindElementByDescription(win, target!.ToLowerInvariant());
            if (el == null) return null;
            try
            {
                if (el.TryGetCurrentPattern(TextPattern.Pattern, out var tp))
                    return ((TextPattern)tp).DocumentRange.GetText(50_000);
                if (el.TryGetCurrentPattern(ValuePattern.Pattern, out var vp))
                    return ((ValuePattern)vp).Current.Value;
            }
            catch { }
            return null;
        }

        // Full-window read
        try
        {
            if (win.TryGetCurrentPattern(TextPattern.Pattern, out var tp))
                return ((TextPattern)tp).DocumentRange.GetText(100_000);
        }
        catch { }

        // Fallback: aggregate all readable values
        var sb = new StringBuilder();
        try
        {
            var all = win.FindAll(TreeScope.Descendants, Condition.TrueCondition);
            foreach (AutomationElement el in all)
            {
                try
                {
                    if (el.TryGetCurrentPattern(ValuePattern.Pattern, out var vp))
                    {
                        var val = ((ValuePattern)vp).Current.Value;
                        if (!string.IsNullOrEmpty(val)) sb.AppendLine(val);
                    }
                }
                catch { }
            }
        }
        catch { }
        return sb.Length > 0 ? sb.ToString() : null;
    }

    /// <summary>
    /// Click a UI element. Prefers InvokePattern; falls back to a
    /// simulated mouse click at the element's bounding-rect centre.
    /// </summary>
    public bool ClickElement(string appName, string target)
    {
        var win = FindWindowForApp(appName.ToLowerInvariant());
        if (win == null) return false;
        var el = FindElementByDescription(win, target.ToLowerInvariant());
        if (el == null) return false;

        // Prefer InvokePattern — no physical mouse movement
        try
        {
            if (el.TryGetCurrentPattern(InvokePattern.Pattern, out var p))
            {
                ((InvokePattern)p).Invoke();
                return true;
            }
        }
        catch { }

        // Fallback: click at bounding-rect centre via Win32
        try
        {
            var rect = el.Current.BoundingRectangle;
            if (!rect.IsEmpty)
            {
                var cx = (int)(rect.X + rect.Width / 2);
                var cy = (int)(rect.Y + rect.Height / 2);
                SetCursorPos(cx, cy);
                System.Threading.Thread.Sleep(50);
                mouse_event(MouseEventF.LeftDown, 0, 0, 0, UIntPtr.Zero);
                System.Threading.Thread.Sleep(50);
                mouse_event(MouseEventF.LeftUp, 0, 0, 0, UIntPtr.Zero);
                return true;
            }
        }
        catch { }
        return false;
    }

    [Flags]
    private enum MouseEventF : uint
    {
        LeftDown = 0x0002,
        LeftUp   = 0x0004,
    }

    [DllImport("user32.dll")]
    private static extern bool SetCursorPos(int x, int y);

    [DllImport("user32.dll")]
    private static extern void mouse_event(MouseEventF dwFlags, int dx, int dy, uint cButtons, UIntPtr dwExtraInfo);

    [DllImport("user32.dll")]
    private static extern bool SetForegroundWindow(IntPtr hWnd);
}
