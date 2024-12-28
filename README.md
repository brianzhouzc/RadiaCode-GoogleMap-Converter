# RadiaCode KML Color Mapper

A Python script that converts RadiaCode KML/KMZ files into color-coded placemarks for visualization in Google Maps/Earth. The script normalizes radiation measurements and assigns colors based on the values using matplotlib colormaps.

## Features

- Supports both KML and KMZ file formats
- Normalizes radiation measurements between specified min/max values
- Customizable color mapping using matplotlib colormaps
- Configurable transparency (alpha) for markers
- Preserves original metadata and measurements
- Outputs color-coded KML file compatible with Google Maps/Earth

## Installation

```bash
pip install pandas matplotlib lxml pykml
```

## Usage

Basic usage:
```bash
python script.py input_file.kmz
```

With optional parameters:
```bash
python script.py input_file.kmz --min 0.05 --max 0.5 --cmap rainbow --alpha 0.8 --output processed.kml
```

### Parameters

- `input_file`: Path to KML/KMZ file (required)
- `--min`: Minimum value for normalization (default: 0.05)
- `--max`: Maximum value for normalization (default: 0.5)
- `--cmap`: Matplotlib colormap name (default: rainbow)
- `--alpha`: Transparency value 0-1 (default: 0.8)
- `--output`: Output file path (optional)

## Output

The script generates a new KML file with:
- Color-coded placemarks based on radiation measurements
- Original timestamp, µSv/h, CPS, and accuracy data preserved
- Compatible format for Google Maps/Earth visualization
