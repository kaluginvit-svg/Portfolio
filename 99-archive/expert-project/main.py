from flask import Flask, render_template, request, redirect, url_for
from openai_module import (
    generate_future_prompts_from_url,
    query_with_custom_system_prompt,
    generate_final_ad_post
)

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        if not url:
            return render_template('index.html', error="URL is required")
        
        try:
            # Step 1: Generate prompts from URL
            prompts_result = generate_future_prompts_from_url(url)
            prompts = prompts_result.get('prompts', [])
            
            # Step 2: Process each prompt and collect results
            analysis_results = []
            for prompt in prompts:
                result = query_with_custom_system_prompt(prompt, url)
                analysis_results.append({
                    'prompt': prompt,
                    'result': result
                })
            
            # Step 3: Generate final ad post
            final_results = [result['result'] for result in analysis_results]
            final_ad = generate_final_ad_post(final_results)
            
            return render_template(
                'index.html',
                url=url,
                prompts=prompts,
                analysis_results=analysis_results,
                final_ad=final_ad
            )
            
        except Exception as e:
            return render_template('index.html', error=str(e))
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True) 