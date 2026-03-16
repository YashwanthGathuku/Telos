using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;
using System.Text.Json;
using Telos.UIGraph.Windows.Models;
using Telos.UIGraph.Windows.Services;
using System.Collections.Concurrent;

var builder = WebApplication.CreateBuilder(args);

// Configure port from environment or default to 8083
var port = Environment.GetEnvironmentVariable("WINDOWS_MCP_PORT") ?? "8083";
builder.WebHost.UseUrls($"http://127.0.0.1:{port}");

builder.Services.AddSingleton<UIAutomationService>();

var app = builder.Build();

var uia = app.Services.GetRequiredService<UIAutomationService>();
var previousSnapshots = new ConcurrentDictionary<string, UISnapshotDto>(StringComparer.OrdinalIgnoreCase);

// Health check
app.MapGet("/health", () => Results.Ok(new { status = "ok", service = "uigraph" }));

// List all visible windows
app.MapGet("/uigraph/windows", () =>
{
    var windows = uia.ListWindows();
    return Results.Ok(windows);
});

// Capture UI snapshot of a specific application
app.MapPost("/uigraph/snapshot", async (HttpContext ctx) =>
{
    var req = await ctx.Request.ReadFromJsonAsync<SnapshotRequest>();
    if (req == null || string.IsNullOrWhiteSpace(req.AppName))
        return Results.BadRequest(new { error = "app_name is required" });

    // Validate input length
    if (req.AppName.Length > 256 || req.Detail.Length > 1000)
        return Results.BadRequest(new { error = "Input too long" });

    var snapshot = uia.CaptureSnapshot(req.AppName);
    if (snapshot == null)
        return Results.NotFound(new { error = $"Window not found: {req.AppName}" });

    // Call the fast capture/delta engine to compute changes (fixes partial gap)
    using var client = new System.Net.Http.HttpClient();
    var deltaUrl = Environment.GetEnvironmentVariable("CAPTURE_ENGINE_URL") ?? "http://127.0.0.1:8084/delta";
    
    try
    {
        previousSnapshots.TryGetValue(req.AppName, out var previousSnapshot);
        var payload = new { old_snapshot = previousSnapshot ?? snapshot, new_snapshot = snapshot };
        var resp = await client.PostAsJsonAsync(deltaUrl, payload);
        previousSnapshots[req.AppName] = snapshot;
        if (resp.IsSuccessStatusCode)
        {
            var deltaResult = await resp.Content.ReadFromJsonAsync<JsonElement>();
            return Results.Ok(new { snapshot, delta = deltaResult });
        }
    }
    catch { /* Swallow connection errors and just return the snapshot if delta engine is offline */ }

    return Results.Ok(new { snapshot });
});

// Focus a window
app.MapPost("/uigraph/focus", async (HttpContext ctx) =>
{
    var req = await ctx.Request.ReadFromJsonAsync<FocusRequest>();
    if (req == null || string.IsNullOrWhiteSpace(req.AppName))
        return Results.BadRequest(new { error = "app_name is required" });

    if (req.AppName.Length > 256)
        return Results.BadRequest(new { error = "Input too long" });

    var success = uia.FocusWindow(req.AppName);
    return Results.Ok(new { success, app = req.AppName });
});

// Launch an application (searches Start Menu, registry App Paths, UWP Store, PATH fallback)
app.MapPost("/uigraph/launch", async (HttpContext ctx) =>
{
    var req = await ctx.Request.ReadFromJsonAsync<LaunchRequest>();
    if (req == null || string.IsNullOrWhiteSpace(req.AppName))
        return Results.BadRequest(new { error = "app_name is required" });

    if (req.AppName.Length > 256 || req.HintExe.Length > 1024)
        return Results.BadRequest(new { error = "Input too long" });

    var hintExe = string.IsNullOrWhiteSpace(req.HintExe) ? null : req.HintExe;
    var result = await uia.LaunchApplication(req.AppName, hintExe);
    return result.Success
        ? Results.Ok(result)
        : Results.NotFound(result);
});

// Perform an action on a UI element
app.MapPost("/uigraph/action", async (HttpContext ctx) =>
{
    var req = await ctx.Request.ReadFromJsonAsync<ActionRequest>();
    if (req == null || string.IsNullOrWhiteSpace(req.AppName))
        return Results.BadRequest(new { error = "app_name is required" });

    // Validate all inputs
    if (req.AppName.Length > 256 || req.Target.Length > 1000 || req.Value.Length > 10000)
        return Results.BadRequest(new { error = "Input too long" });

    bool success = false;

    switch (req.Action.ToLowerInvariant())
    {
        case "write_value":
            success = uia.WriteValue(req.AppName, req.Target, req.Value);
            break;
        case "invoke_button":
            success = uia.InvokeElement(req.AppName, req.Target);
            break;
        case "expand":
            success = uia.ExpandCollapseElement(req.AppName, req.Target);
            break;
        case "select_item":
            success = uia.SelectItem(req.AppName, req.Target);
            break;
        case "toggle":
            success = uia.ToggleElement(req.AppName, req.Target);
            break;
        case "click":
            success = uia.ClickElement(req.AppName, req.Target);
            break;
        case "read_text":
        {
            var textTarget = string.IsNullOrWhiteSpace(req.Target) ? null : req.Target;
            var text = uia.ReadText(req.AppName, textTarget);
            return Results.Ok(new { success = text != null, action = req.Action, app = req.AppName, text });
        }
        default:
            return Results.BadRequest(new { error = $"Unknown action: {req.Action}" });
    }

    return Results.Ok(new { success, action = req.Action, app = req.AppName });
});

app.Run();
