using System.Text.Json.Serialization;

namespace Telos.UIGraph.Windows.Models;

/// <summary>
/// A single UI Automation element extracted from a window.
/// </summary>
public sealed class UIElementDto
{
    [JsonPropertyName("automation_id")]
    public string AutomationId { get; set; } = "";

    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("control_type")]
    public string ControlType { get; set; } = "";

    [JsonPropertyName("value")]
    public string Value { get; set; } = "";

    [JsonPropertyName("bounding_rect")]
    public Dictionary<string, int> BoundingRect { get; set; } = new();

    [JsonPropertyName("children")]
    public List<UIElementDto> Children { get; set; } = new();

    [JsonPropertyName("is_password")]
    public bool IsPassword { get; set; }
}

/// <summary>
/// Snapshot of an application window's accessible UI tree.
/// </summary>
public sealed class UISnapshotDto
{
    [JsonPropertyName("window_title")]
    public string WindowTitle { get; set; } = "";

    [JsonPropertyName("process_name")]
    public string ProcessName { get; set; } = "";

    [JsonPropertyName("process_id")]
    public int ProcessId { get; set; }

    [JsonPropertyName("timestamp")]
    public string Timestamp { get; set; } = DateTime.UtcNow.ToString("o");

    [JsonPropertyName("elements")]
    public List<UIElementDto> Elements { get; set; } = new();
}

/// <summary>
/// Request to capture a snapshot of a specific application.
/// </summary>
public sealed class SnapshotRequest
{
    [JsonPropertyName("app_name")]
    public string AppName { get; set; } = "";

    [JsonPropertyName("detail")]
    public string Detail { get; set; } = "";
}

/// <summary>
/// Request to focus a specific application window.
/// </summary>
public sealed class FocusRequest
{
    [JsonPropertyName("app_name")]
    public string AppName { get; set; } = "";
}

/// <summary>
/// Request to perform an action on a UI element.
/// </summary>
public sealed class ActionRequest
{
    [JsonPropertyName("app_name")]
    public string AppName { get; set; } = "";

    [JsonPropertyName("action")]
    public string Action { get; set; } = "";

    [JsonPropertyName("target")]
    public string Target { get; set; } = "";

    [JsonPropertyName("value")]
    public string Value { get; set; } = "";
}

/// <summary>
/// Request to launch an application by friendly name.
/// </summary>
public sealed class LaunchRequest
{
    [JsonPropertyName("app_name")]
    public string AppName { get; set; } = "";

    /// <summary>Optional direct path to the executable (skips discovery).</summary>
    [JsonPropertyName("hint_exe")]
    public string HintExe { get; set; } = "";
}

/// <summary>
/// Result returned from an application launch attempt.
/// </summary>
public sealed class LaunchResult
{
    [JsonPropertyName("success")]
    public bool Success { get; set; }

    [JsonPropertyName("already_running")]
    public bool AlreadyRunning { get; set; }

    [JsonPropertyName("launch_method")]
    public string LaunchMethod { get; set; } = "";

    [JsonPropertyName("message")]
    public string Message { get; set; } = "";
}
