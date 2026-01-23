"""
Saskatchewan Agricultural Export Dashboard Generator

This script processes agricultural export data for Saskatchewan, applies
classification logic, ranking, and generates an interactive Plotly dashboard.

Key Features:
1. Loads and cleans CSV export data
2. Applies keyword-based classification to group products into families
3. Ranks top 10 products by total export value and labels them
4. Applies a cognitive color palette for visual clarity
5. Generates an interactive stacked bar chart with filtering capabilities

Author: Automated Export Analysis System
Date: 2026-01-23
"""

import pandas as pd
import numpy as np
import json
import base64
import plotly.graph_objects as go
from typing import Dict, List, Tuple

# ============================================================================
# CONSTANTS
# ============================================================================

# CSV file path
CSV_FILE_PATH = "./SK-CN_2024-2025Oct_Report.csv"

# Broad category keyword mapping
BROAD_CATEGORY_KEYWORDS = {
    "Canola Complex": ['rape', 'colza', 'canola'],
    "Wheat Complex": ['wheat', 'durum'],
    "Barley Family": ['barley'],
    "Pulses Complex": ['pea', 'lentil', 'chickpea'],
    "Potash": ['potassium', 'potash'],
    "Wood Pulp": ['wood', 'pulp'],
    "Soya Beans": ['soya']
}

# Color mapping with cognitive logic palette
# Note: Keys use original names without ranking prefixes
COLOR_MAP = {
    # --- 🌻 Canola Complex (Warm/Fire colors - oil & energy) ---
    'Rape/colza seeds,low erucic acid, for oil extraction, w/n broken': '#C62828',
    'Rape/colza seed oil-cake & o solid residue, low erucic acid, w/n ground/pellet': '#EF6C00',
    'Low erucic acid rape (canola) or colza oil and its fractions, crude': '#FFB300',
    'Low erucic acid rape (canola) or colza oil and its fractions, refined': '#FFD600',
    
    # --- 🌾 Wheat Complex (Blue/Marine colors - core trade flow) ---
    'Red spring wheat, o/t certified organic, grade 1, o/t seed for sowing': '#1565C0',
    'Red spring wheat, o/t certified organic, grade 2, o/t seed for sowing': '#42A5F5',
    'Durum wheat, o/t certified organic, o/t seed for sowing': '#455A64',
    
    # --- 🌱 Barley Family (Green/Natural colors - crops) ---
    'Barley, for malting, o/t seed for sowing': '#2E7D32',
    'Barley, o/t certified organic, o/t seed for sowing or malting': '#81C784',
    
    # --- 🟢 Pulses Complex (Earth tones) ---
    'Peas, yellow, nes, dried, shelled, w/n skinned': '#F9A825',
    'Peas, green, nes, dried, shelled, w/n skinned': '#CDDC39',
    'Lentils, dried, shelled, w/n skinned': '#795548',
    
    # --- 💎 Potash (Purple - industry standard) ---
    'Potassium chloride, in packages weighing more than 10 kg': '#9C27B0',
    
    # --- 🌲 Others (Material colors) ---
    'Wood pulp, obtained by a combination of mechanical & chemical pulping processes': '#5D4037',
    'Soya beans,o/t certified organic,for oil extraction,w/n broken,o/t seed f sowing': '#00BCD4'
}

# ============================================================================
# DATA PROCESSING FUNCTIONS
# ============================================================================

def load_and_clean_data(file_path: str) -> pd.DataFrame:
    """
    Load and clean the export data CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Cleaned DataFrame with standardized columns
    """
    print(f"Loading data from {file_path}...")
    
    # Read CSV, skip first row (header placeholder)
    df = pd.read_csv(file_path, skiprows=1)
    
    # Clean column names (remove BOM and whitespace)
    df.columns = [c.replace('\ufeff', '').strip() for c in df.columns]
    
    # Type conversion
    df['Period'] = pd.to_datetime(df['Period'], errors='coerce')
    df['Value ($)'] = pd.to_numeric(df['Value ($)'], errors='coerce')
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
    
    # Split Commodity into HS_Code and Name
    split = df['Commodity'].astype(str).str.split(' - ', n=1, expand=True)
    df['HS_Code'] = split[0]
    df['Name'] = split[1]
    
    # Filter for Saskatchewan province only
    prov = df['Province'].fillna('').astype(str).str.strip().str.casefold()
    df = df[prov == 'saskatchewan'].copy()
    
    # Calculate unit price
    df['Unit_Price'] = np.where(
        (df['Quantity'] > 0) & (~df['Quantity'].isna()),
        df['Value ($)'] / df['Quantity'],
        np.nan
    )
    
    print(f"Data loaded. Rows: {len(df)}")
    return df


def apply_classifications(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply keyword-based classification to assign broad categories.
    
    Args:
        df: DataFrame with 'Name' column
        
    Returns:
        DataFrame with added 'Commodity_Name' and 'Broad_Category' columns
    """
    print("Applying keyword-based classification...")
    
    # Initialize columns
    df['Commodity_Name'] = df['Name']
    df['Broad_Category'] = 'Others'  # Default
    
    def classify_product(name: str) -> str:
        """Classify product based on keyword matching."""
        s = str(name).lower()
        
        # Check for HS code 1514 (oil) in combination with 'oil'
        if '1514' in s and 'oil' in s:
            return "Canola Complex"
        
        # Check each category in priority order
        for category, keywords in BROAD_CATEGORY_KEYWORDS.items():
            if any(keyword in s for keyword in keywords):
                return category
        
        return "Others"
    
    # Apply classification
    df['Broad_Category'] = df['Name'].apply(classify_product)
    
    # Filter out 'Others' category
    initial_count = len(df)
    df = df[df['Broad_Category'] != 'Others'].copy()
    filtered_count = len(df)
    
    print(f"Classification complete. Retained {filtered_count} of {initial_count} rows.")
    return df


def apply_ranking_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rank top 10 products by total value and apply ranking labels.
    
    Args:
        df: DataFrame with classification applied
        
    Returns:
        DataFrame with ranked product names
    """
    print("Applying Top 10 ranking labels...")
    
    # Calculate total value per product
    product_totals = df.groupby('Commodity_Name')['Value ($)'].sum().reset_index()
    product_totals = product_totals.sort_values('Value ($)', ascending=False)
    
    # Get top 10 products
    top_10_products = product_totals.head(10)['Commodity_Name'].tolist()
    
    print(f"Top 10 products by total value:")
    for i, product in enumerate(top_10_products, 1):
        print(f"  #{i}: {product}")
    
    # Create a mapping of original name to ranked name
    name_mapping = {}
    for i, original_name in enumerate(top_10_products, 1):
        ranked_name = f"(Top {i}) {original_name}"
        name_mapping[original_name] = ranked_name
    
    # Apply ranking labels
    df['Commodity_Name_Ranked'] = df['Commodity_Name'].apply(
        lambda x: name_mapping.get(x, x)
    )
    
    # Update color map with ranked names
    updated_color_map = {}
    for key, color in COLOR_MAP.items():
        # Check if this key is in the top 10
        if key in name_mapping:
            updated_color_map[name_mapping[key]] = color
        else:
            updated_color_map[key] = color
    
    # Return both the updated dataframe and color map
    return df, updated_color_map, name_mapping


def get_color_for_commodity(name: str, color_map: Dict, name_mapping: Dict) -> str:
    """
    Get color for a commodity, supporting both exact and fuzzy matching.
    
    Args:
        name: Commodity name (may include ranking prefix)
        color_map: Color mapping dictionary
        name_mapping: Mapping from original to ranked names
        
    Returns:
        Hex color code
    """
    # Check exact match first
    if name in color_map:
        return color_map[name]
    
    # Remove ranking prefix for matching
    clean_name = name
    for i in range(1, 11):
        prefix = f"(Top {i}) "
        if name.startswith(prefix):
            clean_name = name[len(prefix):]
            break
    
    # Check if clean name is in color map
    if clean_name in color_map:
        return color_map[clean_name]
    
    # Fuzzy matching based on keywords
    name_lower = clean_name.lower()
    
    # Canola Complex
    if 'rape' in name_lower or 'colza' in name_lower or 'canola' in name_lower:
        if 'seed' in name_lower and 'oil' not in name_lower:
            return '#C62828'
        elif 'cake' in name_lower or 'residue' in name_lower:
            return '#EF6C00'
        elif 'crude' in name_lower:
            return '#FFB300'
        elif 'refined' in name_lower:
            return '#FFD600'
        else:
            return '#C62828'
    
    # Wheat Complex
    elif 'wheat' in name_lower:
        if 'grade 1' in name_lower or 'grade1' in name_lower:
            return '#1565C0'
        elif 'grade 2' in name_lower or 'grade2' in name_lower:
            return '#42A5F5'
        elif 'durum' in name_lower:
            return '#455A64'
        else:
            return '#1565C0'
    
    # Barley Family
    elif 'barley' in name_lower:
        if 'malting' in name_lower:
            return '#2E7D32'
        else:
            return '#81C784'
    
    # Pulses Complex
    elif 'pea' in name_lower:
        if 'yellow' in name_lower:
            return '#F9A825'
        elif 'green' in name_lower:
            return '#CDDC39'
        else:
            return '#F9A825'
    elif 'lentil' in name_lower:
        return '#795548'
    
    # Potash
    elif 'potassium' in name_lower or 'potash' in name_lower:
        return '#9C27B0'
    
    # Wood Pulp
    elif 'wood pulp' in name_lower or 'pulp' in name_lower:
        return '#5D4037'
    
    # Soya Beans
    elif 'soya' in name_lower or 'soy' in name_lower:
        return '#00BCD4'
    
    # Default neutral color (avoid blue)
    return '#A0A0A0'


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def generate_plot(df: pd.DataFrame, color_map: Dict, name_mapping: Dict) -> go.Figure:
    """
    Generate the interactive Plotly visualization.
    
    Args:
        df: Processed DataFrame with rankings applied
        color_map: Updated color mapping with ranked names
        name_mapping: Mapping from original to ranked names
        
    Returns:
        Plotly Figure object
    """
    print("Generating interactive visualization...")
    
    # Ensure Period is datetime
    if not np.issubdtype(df["Period"].dtype, np.datetime64):
        df["Period"] = pd.to_datetime(df["Period"])
    
    # Group data for visualization
    df_grouped = df.groupby(
        ["Period", "Commodity_Name_Ranked", "Broad_Category"], 
        as_index=False
    )["Value ($)"].sum()
    
    df_total = df.groupby("Period", as_index=False)["Value ($)"].sum()
    
    # Create period strings for x-axis
    df_grouped["Period_str"] = df_grouped["Period"].dt.strftime('%Y-%m')
    df_total["Period_str"] = df_total["Period"].dt.strftime('%Y-%m')
    months = df_total.sort_values("Period")["Period_str"].tolist()
    
    # Create figure
    fig = go.Figure()
    
    # Add bars for each commodity
    commodities_order = sorted(df_grouped["Commodity_Name_Ranked"].unique())
    
    for cname in commodities_order:
        sub = df_grouped[df_grouped["Commodity_Name_Ranked"] == cname].sort_values("Period")
        x_list = sub["Period_str"].tolist()
        y_list = [float(v) if v is not None else None for v in sub["Value ($)"].tolist()]
        broad = sub["Broad_Category"].iloc[0]
        
        # Get color for this commodity
        color = get_color_for_commodity(cname, color_map, name_mapping)
        
        fig.add_trace(
            go.Bar(
                x=x_list,
                y=y_list,
                name=cname,
                marker=dict(color=color),
                legendgroup=broad,
                customdata=[cname] * len(x_list),
                hovertemplate="<b>%{x}</b><br>Commodity: %{customdata}<br>Value: $%{y:,.0f}<extra></extra>"
            )
        )
    
    # Add total trend line
    sub_total = df_total.sort_values("Period")
    x_total = sub_total["Period_str"].tolist()
    y_total = [float(v) if v is not None else None for v in sub_total["Value ($)"].tolist()]
    
    fig.add_trace(
        go.Scatter(
            x=x_total,
            y=y_total,
            name="TOTAL Trend",
            mode="lines+markers",
            line=dict(color="white", width=3, dash="solid"),
            hovertemplate="<b>%{x}</b><br>TOTAL: $%{y:,.0f}<extra></extra>"
        )
    )
    
    # Build dropdown menus for broad category filtering
    names = [trace.name for trace in fig.data]
    name_to_broad = (
        df_grouped.groupby("Commodity_Name_Ranked")["Broad_Category"].first().to_dict()
    )
    broad_categories = sorted(list(df_grouped["Broad_Category"].unique()))
    
    buttons = []
    visible_overview = [True] * len(names)
    buttons.append(
        dict(
            label="Overview (Stacked)",
            method="update",
            args=[{"visible": visible_overview}],
        )
    )
    
    for broad in broad_categories:
        visible = []
        for nm in names:
            if nm == "TOTAL Trend" or name_to_broad.get(nm) == broad:
                visible.append(True)
            else:
                visible.append(False)
        buttons.append(
            dict(
                label=broad,
                method="update",
                args=[{"visible": visible}],
            )
        )
    
    # Update layout
    fig.update_layout(
        updatemenus=[
            dict(
                buttons=buttons,
                direction="down",
                showactive=True,
                x=0,
                xanchor="left",
                y=1.15,
                yanchor="top",
                bgcolor="rgba(0,0,0,0)",
                font=dict(color="white")
            )
        ],
        legend=dict(
            x=1.02,
            y=1,
            xanchor="left",
            yanchor="top",
        ),
        margin=dict(t=120, l=40, r=40, b=40),
        title="Saskatchewan Ag Export Composition (Monthly)",
        title_y=0.95,
        title_x=0.5,
        xaxis=dict(automargin=True),
        yaxis=dict(automargin=True),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        barmode="stack"
    )
    
    fig.update_xaxes(type='category', categoryorder='array', categoryarray=months)
    
    return fig


def save_plot_to_json(fig: go.Figure, output_path: str = "export_data.json"):
    """
    Save the Plotly figure to JSON format.
    
    Args:
        fig: Plotly Figure object
        output_path: Path to save the JSON file
    """
    print(f"Saving visualization to {output_path}...")
    
    # Convert figure to JSON
    fig_json = fig.to_json()
    obj = json.loads(fig_json)
    
    # Decode base64 arrays for better readability
    def decode_array(value):
        if isinstance(value, dict) and "bdata" in value and "dtype" in value:
            arr = np.frombuffer(base64.b64decode(value["bdata"]), dtype=value["dtype"]) 
            return arr.tolist()
        return value
    
    for trace in obj.get("data", []):
        if "x" in trace:
            trace["x"] = decode_array(trace["x"])
        if "y" in trace:
            trace["y"] = decode_array(trace["y"])
    
    # Save to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    
    print(f"Successfully saved to {output_path}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    print("=" * 60)
    print("Saskatchewan Ag Export Dashboard Generator")
    print("=" * 60)
    
    try:
        # Step 1: Load and clean data
        df = load_and_clean_data(CSV_FILE_PATH)
        
        # Step 2: Apply keyword classifications
        df = apply_classifications(df)
        
        # Step 3: Apply Top 10 ranking labels
        df, updated_color_map, name_mapping = apply_ranking_labels(df)
        
        # Step 4: Verify Canola Complex products
        canola_products = df[df['Broad_Category'] == 'Canola Complex']['Commodity_Name'].unique()
        print(f"\nCanola Complex products: {len(canola_products)}")
        for product in canola_products:
            print(f"  - {product}")
        
        if len(canola_products) == 4:
            print("✓ Canola Complex contains all 4 products (including oils)")
        else:
            print(f"⚠ Warning: Canola Complex has {len(canola_products)} products")
        
        # Step 5: Generate visualization
        fig = generate_plot(df, updated_color_map, name_mapping)
        
        # Step 6: Save to JSON
        save_plot_to_json(fig, "export_data.json")
        
        print("\n" + "=" * 60)
        print("Dashboard generation complete!")
        print("=" * 60)
        
    except FileNotFoundError:
        print(f"Error: CSV file not found at {CSV_FILE_PATH}")
        print("Please ensure SK-CN_2024-2025Oct_Report.csv is in the current directory.")
    except Exception as e:
        print(f"Error during execution: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
