# Frequently Asked Questions (FAQ)

### Q1: Why does Video MCP require FFmpeg locally if the video is generated in the cloud?
**A**: While video frames are synthesized in the cloud (Kling, Hailuo, Veo), stitching the individual clips together, adjusting layout aspect ratios, generating and overlaying subtitle captions, and mixing voiceovers with background music are performed locally. This saves cloud rendering bandwidth and gives the server precise frame-level timeline control.

### Q2: What video resolutions and aspect ratios are supported?
**A**: We support `9:16` (vertical reels/TikToks), `16:9` (widescreen landscape), `1:1` (square), and `4:5` (social feed portrait). Video MCP automatically crops, centers, or pads video clips to fit your destination layout.

### Q3: How do I enforce character consistency across scene transitions?
**A**: Use `create_character_profile` with 1 or more reference images (e.g., photos of your subject). This builds a prompt descriptor and stores reference file paths. Then, when calling `generate_scene_with_character` or passing `character_name` to the orchestrator, the server automatically injects character styling and provides the reference image to the Kling model.

### Q4: Can I run this server without ElevenLabs or Kling credentials?
**A**: You can initialize the server, but tools requiring cloud synthesis will return configuration errors. However, the testing suite includes offline mocks and automatic FFmpeg detection, allowing offline development and checks.

### Q5: How do I optimize ElevenLabs character usage costs?
**A**: Keep `VIDEO_MCP_ENABLE_CACHE` set to `true`. This caches voiceovers by script content and voice configuration. Identical narration scripts will be loaded from disk instantly without calling ElevenLabs or consuming characters.
