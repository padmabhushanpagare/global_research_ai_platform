import ollama
import pyttsx3
from config import logger

def generate_briefing_script(structured_data, model_name='llama3'):
    """Uses a local LLM to write a concise, professional broadcast script."""
    
    # 🔴 ADDED: Format variables safely for the audio script prompt
    rev = structured_data.get('revenue_billions')
    eps = structured_data.get('eps')
    guidance = structured_data.get('guidance')
    
    rev_str = f"${rev}B" if rev is not None else "Not disclosed in retrieved context."
    eps_str = f"${eps}" if eps is not None else "Not disclosed in retrieved context."
    guidance_str = guidance if guidance else "No specific operational guidance provided."

    briefing_prompt = f"""
    You are a senior equity research director. Write a sharp, 3-sentence audio briefing script 
    based on these metrics. Format it strictly as a clean text speech block. Do NOT include any 
    introductory text like 'Here is the script'.
    
    Company: {structured_data.get('ticker', 'UNKNOWN')}
    Quarter: {structured_data.get('quarter', 'UNKNOWN')}
    Revenue: {rev_str}
    EPS: {eps_str}
    Guidance: {guidance_str}
    Key Findings: {', '.join(structured_data.get('key_takeaways', []))}
    """
    
    try:
        response = ollama.chat(
            model=model_name,
            messages=[
                {'role': 'system', 'content': 'You generate crisp morning broadcast briefs. No conversational filler. If a metric says "Not disclosed", simply mention that it was not reported rather than reading the exact string.'},
                {'role': 'user', 'content': briefing_prompt}
            ],
            options={'temperature': 0.3} 
        )
        
        clean_text = response['message']['content'].strip()
        if "\n\n" in clean_text:
            clean_text = clean_text.split("\n\n")[-1].replace('"', '').strip()
            
        return clean_text
    except Exception as e:
        logger.error(f"[-] Error generating script: {e}")
        return None
        

def create_audio_briefing(text, output_filename="Analyst_Briefing.wav"):
    """Converts the text script into an offline audio file."""
    try:
        engine = pyttsx3.init()
        
        # Polish the voice settings (optional tuning)
        engine.setProperty('rate', 170) # Slows down the speaking rate slightly for a professional tone
        
        # Generate the file
        engine.save_to_file(text, output_filename)
        engine.runAndWait()
        
        print(f"[=>] Success: Executive audio track saved as '{output_filename}'")
    except Exception as e:
        print(f"[-] Error synthesizing audio: {e}")