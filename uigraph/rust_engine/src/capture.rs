use win_screenshot::capture::capture_display;
use win_screenshot::prelude::*;

/// Capture the primary screen and return PNG bytes.
pub fn capture_primary_screen() -> Result<Vec<u8>, String> {
    // Capture details of the first display
    let buf = capture_display().map_err(|e| format!("Failed to capture display: {:?}", e))?;
    // The win-screenshot capture_display returns an RgbaImage
    
    // We convert it to a dynamic image to save as PNG
    let mut out_bytes = Vec::new();
    let img = image::RgbaImage::from_raw(buf.width, buf.height, buf.pixels)
        .ok_or_else(|| "Failed to construct image from raw bytes".to_string())?;
    
    let dyn_img = image::DynamicImage::ImageRgba8(img);
    dyn_img.write_to(&mut std::io::Cursor::new(&mut out_bytes), image::ImageFormat::Png)
        .map_err(|e| format!("Failed to encode to PNG: {}", e))?;
        
    Ok(out_bytes)
}
