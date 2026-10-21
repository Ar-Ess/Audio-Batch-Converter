# Audio Batch Converter

A Windows desktop application for converting multiple audio files in batches using Audacity. Configure export settings, organize output files, customize filenames, and monitor conversion progress through a graphical interface.

## Why Choose Audio Batch Converter?

Audio Batch Converter is designed for users who value **privacy, transparency, and control over their files**.

- **100% local processing:** Your audio files are processed on your own computer through Audacity. No audio uploads to a conversion server are required.
- **Privacy by design:** Your audio files do not need to leave your computer for conversion. The application is designed to work locally without relying on an online conversion service.
- **Built on Audacity:** Audio processing and exporting are handled by Audacity, an established, open-source audio application.
- **Open-source transparency:** You can inspect the source code to understand how the converter works and what it does with your files.
- **No Python installation required:** The packaged Windows release is ready to run, while Audacity is installed separately.
- **Batch workflow and control:** Convert multiple files with configurable export settings, filename options, output organization, and progress tracking.

Unlike online converters, Audio Batch Converter does not require you to upload your audio to a third-party website. Unlike a complex audio editor, it focuses on making batch conversion straightforward and configurable.

**Your files stay on your computer, your workflow stays under your control, and the source code is available for inspection.**

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configure Audacity](#configure-audacity)
- [How to Use](#how-to-use)
- [Conversion Options](#conversion-options)
- [How It Works](#how-it-works)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [License](#license)

## Features

- **Batch conversion:** Convert multiple audio files in one run.
- **Configurable exports:** Choose supported output formats and available audio settings.
- **Output organization:** Preserve input subfolders or place converted files in a single output folder.
- **Custom filenames:** Configure output filenames using the available naming options.
- **Duplicate handling:** Configure how filename conflicts and existing output files are handled.
- **Progress tracking:** Monitor the current file and overall conversion progress.
- **Error handling:** Report individual conversion failures and continue processing other files when possible.
- **Conversion summary:** Review the results when processing finishes.
- **Persistent settings:** Retain application settings between launches.

## Requirements

- Windows.
- **Audacity 3.7.9**, installed separately.
- Audacity's `mod-script-pipe` scripting module enabled.

**Python is not required** to run the packaged release.

### Why Audacity 3.7.9?

Audio Batch Converter uses Audacity's scripting interface to control audio imports and exports. The release targets Audacity 3.7.9; compatibility with other versions has not been verified.

Download Audacity from the [official Audacity website](https://www.audacityteam.org/).

## Installation

### 1. Download the release

1. Open the repository's [Releases page](../../releases).
2. Download the ZIP archive attached to the desired release.
3. Extract the archive to a folder where you have permission to write files.

Do not run the application directly from inside the ZIP archive.

### 2. Install Audacity

Install Audacity 3.7.9 if it is not already installed.

Audio Batch Converter does not include Audacity. You must install it separately.

### 3. Enable Audacity scripting

Follow the instructions in [Configure Audacity](#configure-audacity) below.

### 4. Launch the application

Run:

`StartAudioConverter.bat`

On the first launch, the launcher asks you to locate the `Audacity.exe` executable. Select the executable belonging to your Audacity 3.7.9 installation. If you are not used to locate .exe files, please check your "C:/Program Files" folder on your computer, as it is the usual location for an Audacity installation.

The selected path is saved in the local configuration folder for subsequent launches.

Keep the release files together. In particular, do not separate `AudioBatchConverter.exe` from its `_internal` folder.

## Configure Audacity

Audio Batch Converter communicates with Audacity through its named-pipe scripting interface. The `mod-script-pipe` module must be enabled for this communication to work.

1. Open Audacity.
2. Open **Edit → Preferences**.
3. Navigate to the **Modules** section.
4. Locate `mod-script-pipe` and enable it.
5. Apply the changes and close Audacity.
6. Restart Audacity.

The exact preference layout may vary slightly by installation.

After enabling the module, close Audacity before launching Audio Batch Converter. The launcher expects Audacity not to be running already, then starts it and waits for the scripting pipes to become available.

If the pipes are not available, check the troubleshooting section below.

## How to Use

1. Run `StartAudioConverter.bat`.
2. If prompted, select your `Audacity.exe`.
3. Choose the input files or input folder using the application's interface.
4. Select the output folder.
5. Configure the desired output format and audio settings.
6. Choose the output organization, naming, and duplicate-file behavior.
7. Start the conversion.
8. Monitor the progress indicator and current file.
9. Review the final summary for successful conversions and errors.

The exact options available depend on the installed release and the export capabilities available in Audacity.

## Conversion Options

### General Options

The application provides the following options to control which files are converted and how the output is organized:

- **Include files in subfolders** — Include files located in subfolders when processing an input folder.
- **Keep folder structure** — Preserve the original folder hierarchy in the output folder.
- **Set new filenames** — Customize the filenames of converted files.
- **Overwrite existing output files** — Allow existing output files to be overwritten.
- **Skip files with the same extension as output** — Skip files that already have the selected output file extension.

### Audio Options

Customize the exported audio format and its properties using the available settings. These options depend on the selected output format.

- **Output format** — Choose the audio format for the converted files.
- **Sample rate** — Set the sample rate of the exported audio where supported.
- **Bit depth** — Select the bit depth for formats that support it, including available integer or floating-point PCM options.
- **Format-specific settings** — Configure additional export parameters available for the selected format.

### Additional Features

In addition to the general options, the application includes features to make batch conversion easier to manage:

- **Handle duplicate filenames** — Manage filename conflicts when multiple input files would produce the same output filename.
- **Continue after errors** — Continue processing the remaining files if an individual conversion fails.
- **Show progress** — Display conversion progress, including the current file and overall progress.

## How It Works

Audio Batch Converter provides the graphical interface and coordinates the conversion workflow, while Audacity performs the audio import and export operations.

At a high level, the workflow is:

1. The application validates the selected input and output locations.
2. It prepares the output path and filename for each file.
3. It communicates with Audacity through the scripting pipe.
4. Audacity imports and exports the audio using the selected settings.
5. The application checks the result, records errors, and updates progress.
6. The application presents a final summary.

This approach uses Audacity's existing audio-processing and export capabilities instead of implementing its own audio codecs.

## Troubleshooting

### The application cannot find Audacity

Run `StartAudioConverter.bat` and select the correct `Audacity.exe` when prompted.

If the saved path is no longer valid, remove:

`config\audacity_path.txt`

Then launch the application again to select the executable.

### Audacity scripting pipes are unavailable

Check that `mod-script-pipe` is enabled in Audacity's preferences. Restart Audacity after enabling it.

If the problem persists, verify that you are using the supported Audacity version and that the application is not blocked by security software.

### Audacity is already running

Close all running Audacity instances before launching Audio Batch Converter. The launcher checks for an existing Audacity process.

### A conversion fails

Check the error reported by the application. Verify that the source file can be opened by Audacity, the output directory is writable, and the selected export format is supported.

Some formats may require additional export libraries or components in Audacity.

### The application does not start

Make sure the extracted release contains both:

- `AudioBatchConverter.exe`
- The `_internal` folder and its contents

Keep the release folder structure intact. Do not distribute or run the executable on its own.

## Development

The repository separates development files from packaged release files:

```text
Audio-Batch-Converter-Github/
├── Development/
│   ├── StartAudioConverter.bat
│   └── main.py
├── Release/
│   ├── StartAudioConverter.bat
│   └── Internal/
│       ├── AudioBatchConverter.exe
│       └── _internal/
├── Build.bat
├── BuildInstructions.txt
└── README.md
```

### Build a release

1. Install Python 3.10.11 and PyInstaller in the development environment.
2. Open the repository folder.
3. Run `Build.bat`.
4. Wait for the build to complete.
5. Test the application using `Release\StartAudioConverter.bat`.

The build script generates a packaged Windows application from `Development\main.py` and places the executable and its runtime files in `Release\Internal`.

End users do not need Python installed.

## License

Add the project's license here before distributing it publicly. Also review the licensing requirements for any third-party libraries and components included in the release.
