import csv
import pandas as pd

def clean_csv():
    print("🧹 Cleaning CSV - Extracting Brand Name and Size only")
    print("=" * 50)
    
    # Read the systematic CSV file
    input_file = "systematic_brand_details.csv"
    output_file = "clean_brand_size.csv"
    
    try:
        # Read the CSV using pandas
        df = pd.read_csv(input_file)
        print(f"✅ Read {len(df)} records from {input_file}")
        
        # Extract only Brand and Size columns
        clean_df = df[['Brand', 'Size']].copy()
        
        # Remove duplicates
        clean_df = clean_df.drop_duplicates()
        print(f"✅ Removed duplicates, now have {len(clean_df)} unique records")
        
        # Sort by Brand name
        clean_df = clean_df.sort_values('Brand')
        
        # Save to new CSV
        clean_df.to_csv(output_file, index=False)
        print(f"✅ Saved clean data to {output_file}")
        
        # Show sample data
        print(f"\n📋 Sample clean data (first 10 records):")
        for i, row in clean_df.head(10).iterrows():
            print(f"  {row['Brand']} | {row['Size']}")
        
        print(f"\n📊 Summary:")
        print(f"  Total unique brand-size combinations: {len(clean_df)}")
        print(f"  Unique brands: {clean_df['Brand'].nunique()}")
        print(f"  Unique sizes: {clean_df['Size'].nunique()}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    clean_csv() 