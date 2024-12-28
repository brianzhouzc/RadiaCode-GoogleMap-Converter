import argparse
import io
import re
import zipfile
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from lxml import etree
from pykml import parser
from pykml.factory import KML_ElementMaker as KML


def parse_description(desc):
    pattern = r'<b>(.*?)</b></br>([\d.]+) µSv/h</br>([\d.]+) cps</br>Accuracy: ±(\d+) m</br>'
    match = re.search(pattern, desc)
    if match:
        return pd.Series({
            'datetime': match.group(1),
            'usvh': float(match.group(2)),
            'cps': float(match.group(3)),
            'accuracy': match.group(4)
        })
    return pd.Series({'datetime': None, 'usvh': None, 'cps': None, 'accuracy': None})

def get_color(value, cmap_name, alpha=0.8):
    cmap = plt.get_cmap(cmap_name)
    r, g, b, _ = cmap(value)

    return f"{int(alpha * 255):02x}{int(b * 255):02x}{int(g * 255):02x}{int(r * 255):02x}".upper()

def read_kml_content(file_path):
    """Read KML content from either KML or KMZ file"""
    file_path = Path(file_path)

    if file_path.suffix.lower() == '.kmz':
        with zipfile.ZipFile(file_path) as kmz:
            # Find doc.kml in the archive
            kml_filename = next((name for name in kmz.namelist() if name.endswith('.kml')), None)
            if not kml_filename:
                raise ValueError("No KML file found in KMZ archive")

            with kmz.open(kml_filename) as kml_file:
                kml_content = kml_file.read()
                return parser.parse(io.BytesIO(kml_content))
    else:
        with open(file_path, 'rb') as f:
            return parser.parse(f)

def process_kml(file_path, min_val, max_val, cmap_name, alpha):
    # Read KML/KMZ file
    doc = read_kml_content(file_path)
    root = doc.getroot()

    name = root.Document.name
    description = root.Document.description

    # Extract placemarks
    placemarks = []
    for placemark in root.Document.findall(".//Placemark"):
        placemarks.append({
            "id": placemark.get('id'),
            "style_url": placemark.styleUrl.text,
            "coordinates": placemark.Point.coordinates.text,
            "description": placemark.description.text
        })

    # Create DataFrame
    df = pd.DataFrame(placemarks)

    # Parse description
    df[['datetime', 'usvh', 'cps', 'accuracy']] = df['description'].apply(parse_description)

    # Normalize values
    df['usvh_normalized'] = df['usvh'].apply(
        lambda x: min(max((x - min_val) / (max_val - min_val), 0), 1)
    )

    # Generate colors
    df['color'] = df['usvh_normalized'].apply(lambda x: get_color(x, cmap_name, alpha))

    return (df, name, description)

def create_kml_from_dataframe(df, name=None, description=None):
    name = name if name else datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    description = description if description else f"Points: {len(df)}/{len(df)}"

    # Create the root KML document
    doc = KML.kml(
        KML.Document(
            KML.name(name),
            KML.description(description)
        )
    )

    # Add placemarks for each row in the dataframe
    for _, row in df.iterrows():
        # Create the style for the placemark
        style = KML.Style(
            KML.IconStyle(
                KML.color(row['color']),
                KML.scale("0.8"),
                KML.Icon(
                    KML.href("https://maps.google.com/mapfiles/kml/pal2/icon18.png")
                )
            )
        )

        # Create extended data
        extended_data = KML.ExtendedData(
            KML.Data(
                KML.value(row['datetime']),
                name="Time"
            ),
            KML.Data(
                KML.value(f"{row['usvh']:.2f}"),
                name="µSv/h"
            ),
            KML.Data(
                KML.value(f"{row['cps']:.1f}"),
                name="cps"
            ),
            KML.Data(
                KML.value(str(int(row['accuracy']))),
                name="Accuracy (m)"
            )
        )

        # Extract coordinates
        coords = row['coordinates'].split(',')
        longitude, latitude = float(coords[0]), float(coords[1])

        # Create the placemark
        placemark = KML.Placemark(
            style,
            extended_data,
            KML.Point(
                KML.coordinates(f"{longitude},{latitude},0")
            )
        )
        placemark.set('id', str(row['id']))

        # Add the placemark to the document
        doc.Document.append(placemark)

    # Convert to string and save
    kml_str = etree.tostring(doc, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    return kml_str
  

def main():
    parser = argparse.ArgumentParser(description='Convert RadiaCode KML/KMZ files into color-coded placemarks for Google Maps/Earth')
    parser.add_argument('input_file', type=str, help='Path to the KML or KMZ file')
    parser.add_argument('--min', type=float, default=0.05, help='Minimum value for normalization (default: 0.05)')
    parser.add_argument('--max', type=float, default=0.5, help='Maximum value for normalization (default: 0.5)')
    parser.add_argument('--cmap', type=str, default='rainbow', help='Matplotlib colormap (default: rainbow)')
    parser.add_argument('--alpha', type=float, default=0.8, help='Alpha value (default: 0.8)')
    parser.add_argument('--output', type=str, help='Output file path (include filename)')

    args = parser.parse_args()

    # Validate file path
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: File {input_path} does not exist")
        return

    # Validate file extension
    if input_path.suffix.lower() not in ['.kml', '.kmz']:
        print(f"Error: File must be .kml or .kmz format")
        return

    try:
        # Process the data
        df, name, description = process_kml(input_path, args.min, args.max, args.cmap, args.alpha)

        # Output handling
        if args.output:
            output_path = Path(args.output)
            if not output_path.suffix:
                output_path = output_path.with_suffix('.kml')
        else:
            output_path = input_path.with_stem(f"{input_path.stem}_processed").with_suffix('.kml')

        kml_str = create_kml_from_dataframe(df, name, description)
        with open(output_path, 'wb') as f:
            f.write(kml_str)

    except Exception as e:
        print(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()
