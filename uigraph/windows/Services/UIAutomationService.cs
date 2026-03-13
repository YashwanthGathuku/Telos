using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Windows.Automation;
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

    [DllImport("user32.dll")]
    private static extern bool SetForegroundWindow(IntPtr hWnd);
}
