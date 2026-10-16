import json
import whisper
from gtts import gTTS
from IPython.display import Audio, display
import os

# Whisper 'base' is a good speed/accuracy trade-off for short reports
model = whisper.load_model("base")

def load_appraisal_json(json_path):
    with open(json_path, 'r') as f:
        return json.load(f)

def format_appraisal_text(data):
    text_parts = []
    
    # Property Information
    prop = data.get("property", {})
    text_parts.append(f"Property appraisal summary for {prop.get('name', 'Unknown Property')}.")
    text_parts.append(f"This property has {prop.get('total_units', 0)} units on {prop.get('acres', 0)} acres.")
    
    # Valuation
    val = data.get("valuation", {})
    final_val = val.get("final_value", 0)
    text_parts.append(f"The final appraised value as of {val.get('effective_date', 'unknown date')} is ${final_val:,.0f}.")
    text_parts.append(f"Sales comparison value: ${val.get('sales_comparison_value', 0):,.0f}.")
    text_parts.append(f"Income approach value: ${val.get('income_approach_value', 0):,.0f}.")
    
    # Financials
    fin = data.get("financials", {})
    text_parts.append(f"Financial summary: Potential gross income is ${fin.get('potential_gross_income', 0):,.0f}.")
    text_parts.append(f"Vacancy rate is {fin.get('vacancy_rate', 0)}%.")
    text_parts.append(f"Total expenses: ${fin.get('total_expenses', 0):,.0f}.")
    text_parts.append(f"Capitalization rate: {fin.get('cap_rate', 0)}%.")
    text_parts.append(f"Expense ratio: {fin.get('expense_ratio', 0)}%.")
    
    # Expenses
    exp = data.get("expenses", {})
    text_parts.append(f"Annual property taxes: ${exp.get('property_taxes', 0):,.0f}.")
    text_parts.append(f"Insurance: ${exp.get('insurance', 0):,.0f}.")
    text_parts.append(f"Management fee: {exp.get('management', 0)}%.")
    
    # Unit Mix Summary
    units = data.get("unit_mix", [])
    text_parts.append(f"The property has {len(units)} different unit types.")
    for i, unit in enumerate(units[:5], 1):  
        beds = unit.get('bedrooms', 0)
        baths = unit.get('bathrooms', 0)
        rent = unit.get('rent', 0)
        count = unit.get('count', 0)
        if count > 0 and count < 100:  
            text_parts.append(f"Unit type {i}: {count} units with {beds} bedrooms, {baths} bathrooms, renting at ${rent} per month.")
    
    # Comparables Summary
    comps = data.get("comparables", [])
    valid_comps = [c for c in comps if c.get('price', 0) > 100000] 
    text_parts.append(f"There are {len(valid_comps)} comparable properties.")

    for i, comp in enumerate(valid_comps[:3], 1):  
        addr = comp.get('address', 'Unknown address')
        price = comp.get('price', 0)
        ppu = comp.get('price_per_unit', 0)
        text_parts.append(f"Comparable {i} at {addr}: Sale price ${price:,.0f}, price per unit ${ppu:,.0f}.")
    


    text_parts.append("End of appraisal summary.")
    return " ".join(text_parts)



def text_to_speech(text, output_path="appraisal_report.mp3", lang='en', slow=False):
    tts = gTTS(text=text, lang=lang, slow=slow)
    tts.save(output_path)
    print(f"Saved TTS output to: {output_path}")
    return output_path

def transcribe_audio(audio_path):
    result = model.transcribe(audio_path)
    return result["text"]

def process_appraisal_to_speech(json_path, output_audio="appraisal_output.mp3", play=True):
  
    data = load_appraisal_json(json_path)
    print("JSON loaded successfully")
    speech_text = format_appraisal_text(data)
    print(f" Generated {len(speech_text)} characters of text")
    print(f"\nPreview of audio: {speech_text[:200]}...\n")
    
    print(" Generating speech audio...")
    audio_path = text_to_speech(speech_text, output_audio)
    
    if play:
        display(Audio(audio_path, autoplay=False))
    
    return {"json_data": data, "speech_text": speech_text, "audio_file": audio_path}

def transcribe_then_convert(input_audio, output_audio="transcribed_output.mp3"):
  
    print(f"\n Transcribing audio: {input_audio}")
    transcription = transcribe_audio(input_audio)
    audio_path = text_to_speech(transcription, output_audio)
    display(Audio(audio_path, autoplay=False))
    
    return {"transcription": transcription, "audio_file": audio_path}

if __name__ == "__main__":
    import sys
    process_appraisal_to_speech(sys.argv[1] if len(sys.argv) > 1 else "appraisal_data.json", play=False)