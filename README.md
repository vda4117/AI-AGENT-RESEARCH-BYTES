# AI-AGENT-RESEARCH-BYTES
AI agent for research on given research topics and send research details to provided email id.

## Tech Stack:
- Language: Python
- Framework: OpenAI Agents SDK  (https://openai.github.io/openai-agents-python/)
- LLM model: gemini-2.0-flash
- Web Interface: Gradio
- Email delivery platform: Sendgrid 
- Deployment: Huggingface Spaces

We used OpenAI Agents SDK to research on given topic and send email with the detail on that topic. Please find more about OpenAI Agents SDK at https://openai.github.io/openai-agents-python/



## Setups:
- Hopefully Python is already available on your pc.
- Install all the packages/library available in requirements.txt
- Create the GEMINI API KEY. 
	-- Go to https://aistudio.google.com/app/apikey and click on create api key.
	-- Ues gemini-2.0-flash llm model. It is free till some limit. So it will not charge anything. 
-  To send email we used Sendgrid. 
	-- Go to https://app.sendgrid.com and sign-up.
	-- Go to https://app.sendgrid.com/settings/api_keys and click on create api key.
	-- Go to https://app.sendgrid.com/settings/sender_auth and click on verify single sender and varify the email id that you use to send email.


## And now for deployment

This code is in `banking_bytes.py`

We will deploy to HuggingFace Spaces. 
1. Visit https://huggingface.co and set up an account  
2. From the Avatar menu on the top right, choose Access Tokens. Choose "Create New Token". Give it WRITE permissions.
3. Take this token and add it to your .env file: `HF_TOKEN=hf_xxx` and see note below if this token doesn't seem to get picked up during deployment  
4. From the base folder, enter: `uv run gradio deploy` and if for some reason this still wants you to enter your HF token, then interrupt it with ctrl+c and run this instead: `uv run dotenv -f .env run -- uv run gradio deploy` which forces your keys to all be set as environment variables   
5. Follow its instructions: name it like "banking_bytes" or any other name you prefer, then specify banking_bytes.py, choose cpu-basic as the hardware, say Yes to needing to supply secrets, provide your GOOGLE_API_KEY, your SENDGRID_API_KEY and say "no" to github actions.  
Note: If README.md available before your deployment in base directory then delete it. The requirements.txt file should have all the required 3rd party packes that need to import.


#### More about these secrets:

If you're confused by what's going on with these secrets: it just wants you to enter the key name and value for each of your secrets -- so you would enter:  
`GOOGLE_API_KEY`  
Followed by:  
`your_api_key_value`  

And if you don't want to set secrets this way, or something goes wrong with it, it's no problem - you can change your secrets later:  
1. Log in to HuggingFace website  
2. Go to your profile screen via the Avatar menu on the top right  
3. Select the Space you deployed  
4. Click on the Settings wheel on the top right  
5. You can scroll down to change your secrets, delete the space, etc.

