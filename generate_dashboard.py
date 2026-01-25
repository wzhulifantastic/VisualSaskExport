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
Date: 2026-01-25
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
    df['HS_Code'] = split[0].str.strip()
    df['Name'] = split[1].str.strip()
    
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


def apply_naming_conventions(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict, Dict]:
    """
    Apply HS Code naming conventions to ALL products.
    Top 10 items get (Top X) prefix.
    
    Format:
      Top 10: "(Top X) [HS 1234] Name"
      Others: "[HS 1234] Name"
    
    Args:
        df: DataFrame with classification applied
        
    Returns:
        Tuple of (DataFrame with ranked product names, updated color map, name mapping)
    """
    print("Applying global HS Code naming conventions...")
    
    # Create Name -> HS_Code mapping
    # Note: Assuming 'Commodity_Name' is unique per product
    name_hs_map = df.drop_duplicates('Commodity_Name').set_index('Commodity_Name')['HS_Code'].to_dict()
    
    # Calculate total value per product for ranking
    product_totals = df.groupby('Commodity_Name')['Value ($)'].sum().reset_index()
    product_totals = product_totals.sort_values('Value ($)', ascending=False)
    
    # Get top 10 products
    top_10_products = product_totals.head(10)['Commodity_Name'].tolist()
    
    # Create a mapping of original name to new formatted name
    name_mapping = {}
    
    # Get all unique products
    all_products = df['Commodity_Name'].unique()
    
    for product in all_products:
        hs_code = name_hs_map.get(product, 'N/A')
        
        if product in top_10_products:
            rank = top_10_products.index(product) + 1
            new_name = f"(Top {rank}) [HS {hs_code}] {product}"
        else:
            new_name = f"[HS {hs_code}] {product}"
            
        name_mapping[product] = new_name

    # Apply naming to DataFrame
    df['Commodity_Name_Ranked'] = df['Commodity_Name'].apply(
        lambda x: name_mapping.get(x, x)
    )
    
    # Update color map with ranked names to ensure exact matches work
    updated_color_map = {}
    for key, color in COLOR_MAP.items():
        # key is the original name. If it has been mapped, use the new name as key.
        if key in name_mapping:
            updated_color_map[name_mapping[key]] = color
        else:
            updated_color_map[key] = color
            
    return df, updated_color_map, name_mapping


def generate_sorted_commodities_list(df: pd.DataFrame) -> List[str]:
    """
    Generate a sorted list of commodities by Double Descending logic:
    1. Broad Category Total Value (Descending)
    2. Product Total Value within Category (Descending)
    
    This results in the Highest Value items (e.g., Canola) being at the START of the list.
    
    Args:
        df: DataFrame with 'Commodity_Name_Ranked', 'Broad_Category', 'Value ($)'
        
    Returns:
        List of sorted commodity names (Highest Value First)
    """
    print("Generating hierarchical sorted commodities list (Double Descending)...")
    
    # 1. Calculate broad category totals and sort in DESCENDING order
    broad_totals = df.groupby('Broad_Category')['Value ($)'].sum().sort_values(ascending=False).index.tolist()
    
    sorted_commodities = []
    for broad in broad_totals:
        # 2. Within each broad category, sort products by value in DESCENDING order
        sub_df = df[df['Broad_Category'] == broad]
        prod_sorted = sub_df.groupby('Commodity_Name_Ranked')['Value ($)'].sum().sort_values(ascending=False).index.tolist()
        sorted_commodities.extend(prod_sorted)
    
    return sorted_commodities


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
    
    # Remove ranking prefix and HS code for matching
    clean_name = name
    for i in range(1, 11):
        prefix = f"(Top {i}) [HS "
        if name.startswith(prefix):
            # Find the end of HS code
            end_hs = name.find('] ', len(prefix))
            if end_hs != -1:
                clean_name = name[end_hs + 2:]
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

def generate_plot(df: pd.DataFrame, color_map: Dict, name_mapping: Dict, sorted_commodities: List[str]) -> go.Figure:
    """
    Generate an interactive stacked bar chart.
    
    Visual Logic:
    1. Dark Mode Compatible: Force white text and transparent background.
    2. Strict Hierarchy: Ensures the highest value items are visually at the top
       of both the stack and the legend.
    
    Args:
        df: DataFrame containing export data
        color_map: Dictionary mapping product names to hex colors
        name_mapping: Dictionary mapping original names to display names
        sorted_commodities: List of products sorted by value (Highest -> Lowest)
        
    Returns:
        Plotly Figure object
    """
    print("Generating interactive visualization...")
    
    # Data Preparation
    # Format dates as "YYYY<br>Mon" for vertical stacking (e.g., 2025<br>Oct)
    df["Period_str"] = df["Period"].dt.strftime('%Y<br>%b')
    months = df.sort_values("Period")["Period_str"].unique().tolist()
    
    # Group data for plotting
    df_grouped = df.groupby(["Period", "Commodity_Name_Ranked", "Broad_Category", "Period_str"], as_index=False)["Value ($)"].sum()
    df_total = df.groupby(["Period", "Period_str"], as_index=False)["Value ($)"].sum()

    # Calculate category ranking for dropdown menu (Highest Value -> Lowest Value)
    category_rank = df.groupby("Broad_Category")["Value ($)"].sum().sort_values(ascending=False).index.tolist()
    
    fig = go.Figure()

    def smart_wrap(text: str, max_chars: int = 20) -> str:
        """
        Insert a line break (<br>) at the first space after max_chars.
        Avoids cutting words in the middle.
        """
        if len(text) <= max_chars:
            return text
        split_idx = text.find(' ', max_chars)
        if split_idx == -1:
            return text
        return text[:split_idx] + "<br>" + text[split_idx+1:]

    # Core Plotting Loop:
    # We iterate through 'sorted_commodities' in REVERSE (Smallest -> Largest).
    # Why? Plotly builds stacked bars from bottom to top.
    # By adding the smallest items first, the largest item (last added) appears
    # physically at the TOP of the stack, matching our visual hierarchy goal.
    for cname in reversed(sorted_commodities):
        if cname not in df_grouped["Commodity_Name_Ranked"].values:
            continue
        
        sub = df_grouped[df_grouped["Commodity_Name_Ranked"] == cname].sort_values("Period")
        display_name = smart_wrap(cname, max_chars=20)
        
        # Calculate explicit rank for Legend sorting
        # sorted_commodities[0] is Highest Value -> Index 0 -> Smallest Rank Number
        # Plotly 'legendrank' sorts ascending (Low rank = Top of legend)
        rank_val = sorted_commodities.index(cname)

        fig.add_trace(go.Bar(
            x=sub["Period_str"],
            y=sub["Value ($)"],
            name=display_name,
            marker=dict(color=get_color_for_commodity(cname, color_map, name_mapping)),
            legendgroup=sub["Broad_Category"].iloc[0],
            legendrank=rank_val,  # Force legend order to match Value Rank
            customdata=[cname] * len(sub),
            hovertemplate="<b>%{x}</b><br>%{customdata}<br>Value: $%{y:,.0f}<extra></extra>"
        ))

    # Add Total Trend Line (White)
    sub_total = df_total.sort_values("Period")
    fig.add_trace(go.Scatter(
        x=sub_total["Period_str"], y=sub_total["Value ($)"],
        name="TOTAL Trend", mode="lines+markers",
        legendrank=9999,  # Force trend line to the very bottom of legend
        line=dict(color="white", width=3)
    ))

    # Layout Configuration
    fig.update_layout(
        height=800,
        barmode="stack",
        
        # Transparent background
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        
        # Global font settings (White for Dark Mode compatibility)
        font=dict(color="white", size=12),
        
        legend=dict(
            # Using 'grouped' mode because explicit 'legendrank' controls the order
            traceorder="grouped",
            tracegroupgap=40,
            font=dict(size=13, color="white"),
            x=1.02, y=1,
            xanchor="left", valign="top",
            bgcolor="rgba(0,0,0,0)"
        ),
        
        # Margin adjustment to fit legend
        margin=dict(t=100, l=60, r=350, b=150),
        
        xaxis=dict(
            type='category',
            categoryorder='array',
            categoryarray=months,
            tickangle=0,
            tickfont=dict(color="white"),
            rangeslider=dict(visible=True, thickness=0.06),
            # Default Zoom: Show approximately the last 10 months
            range=[len(months) - 10.5, len(months) - 0.5] if len(months) > 10 else None,
            gridcolor="rgba(255,255,255,0.1)"
        ),
        
        yaxis=dict(
            title=dict(text="Export Value ($)", font=dict(color="white")),
            tickfont=dict(color="white"),
            tickformat="$s",  # SI Units (e.g., $1.5M)
            gridcolor="rgba(255,255,255,0.1)"
        ),
        
        # Dropdown Menu Configuration
        updatemenus=[dict(
            bgcolor="white",  # Ensure visibility against dark backgrounds
            buttons=[
                dict(label="Overview", method="update", args=[{"visible": [True]*len(fig.data)}])
            ] + [
                dict(label=broad, method="update", args=[{"visible": [t.legendgroup==broad or t.name=="TOTAL Trend" for t in fig.data]}])
                for broad in category_rank 
            ],
            font=dict(color="black"),
            x=0, y=1.12, showactive=True
        )]
    )

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
        # Load and process data
        df = load_and_clean_data(CSV_FILE_PATH)
        df = apply_classifications(df)
        df, updated_color_map, name_mapping = apply_naming_conventions(df)
        sorted_commodities = generate_sorted_commodities_list(df)
        
        # Generate visualization
        fig = generate_plot(df, updated_color_map, name_mapping, sorted_commodities)
        
        # Save output
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
