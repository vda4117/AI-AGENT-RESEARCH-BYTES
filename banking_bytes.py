import os
from typing import Dict
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel, Agent, WebSearchTool, ModelSettings, function_tool, Runner, trace, gen_trace_id
from dotenv import load_dotenv
import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from pydantic import BaseModel, Field
import asyncio
import gradio as gr




load_dotenv(override=True)

google_api_key = os.getenv('GOOGLE_API_KEY')
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)
gemini_model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=gemini_client)


################################### Email ###############################
@function_tool
def send_email(subject: str, html_body: str, to_emails: str) -> Dict[str, str]:
    """ Send an email with the given subject and HTML body to given receipent"""
    print(f'send email to {to_emails}')
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email("ltimbb2025@outlook.com") # put your verified sender here
    to_email = To(to_emails) # put your recipient here
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    response = sg.client.mail.send.post(request_body=mail)
    print("Email response", response.status_code)
    return {"status": "success"}

INSTRUCTIONS = f"""You are able to send a nicely formatted HTML email based on a detailed report. The email should be attractive like it 
can include tables. You will be provided with a detailed report and receipent email id. 
You should use your tool to send one email, providing the report converted into clean, well presented HTML with an appropriate subject line. 
Always give heading as Banking Bytes.
"""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model=gemini_model,
)




################################ Planner #####################################
no_of_searchs = 4

INSTRUCTIONS = f"You are a helpful research assistant. Given a query, come up with a set of web searches \
to perform to best answer the query. Output {no_of_searchs} terms to query for."


class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")
    
planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model=gemini_model,
    output_type=WebSearchPlan,
)


############################# Search ###################################
INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write succintly, no need to have complete sentences or good "
    "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
    "essence and ignore any fluff. Do not include any additional commentary other than the summary itself."
)

search_agent = Agent(
    name="Search agent",
    instructions=INSTRUCTIONS,
    # tools=[WebSearchTool(search_context_size="low")],
    model=gemini_model,
    model_settings=ModelSettings(tool_choice="required"),
)



###################### Write ####################################
INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query, and some initial research done by a research assistant.\n"
    "You should first come up with an outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, it should be in attractive format so use tables if needed"
    "and it should be lengthy and detailed. Aim for at least 300 words. It also have to_emails field that have receivers email id"
)


class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")

    markdown_report: str = Field(description="The final report")

    to_emails: str = Field(description="The email id of receiver")

    follow_up_questions: list[str] = Field(description="Suggested topics to research further")


writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model=gemini_model,
    output_type=ReportData,
)

###################################### Research ####################################
class ResearchManager:

    async def run(self, query: str, to_emails: str):
        """ Run the deep research process, yielding the status updates and the final report"""
        print("Starting research...")
        search_plan = await self.plan_searches(query)
        yield "Searches planned, starting to search..."     
        search_results = await self.perform_searches(search_plan)
        yield "Searches complete, writing report..."
        report = await self.write_report(query, search_results, to_emails)
        yield "Report written, sending email..."
        print(f'the email id in  report is {report.to_emails}')
        await self.send_email(report)
        yield "Email sent, research complete"
        yield report.markdown_report
        
        

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        print("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """ Perform the searches to perform for the query """
        print("Searching...")
        num_completed = 0
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed")
        print("Finished searching")
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        """ Perform a search for the query """
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            return str(result.final_output)
        except Exception:
            return None

    async def write_report(self, query: str, search_results: list[str], to_emails: str) -> ReportData:
        """ Write the report for the query """
        print("Thinking about report...")
        input = f"Original query: {query}\nSummarized search results: {search_results}\n receiver email id: {to_emails}"
        result = await Runner.run(
            writer_agent,
            input,
        )

        print("Finished writing report")
        return result.final_output_as(ReportData)
    
    async def send_email(self, report: ReportData) -> None:
        print("Writing email...")
        result = await Runner.run(
            email_agent,
            report.markdown_report+" "+report.to_emails,
        )
        print("Email sent")
        return report


########################### Deep Research ##########################
if __name__ == "__main__":
    async def run(query: str, to_emails: str):
        async for chunk in ResearchManager().run(query, to_emails):
            yield chunk


    with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
        gr.Markdown("# Banking Bytes")
        to_emails = gr.Textbox(label="Your Email ID")
        query_textbox = gr.Textbox(label="Today's Topic for Banking Bytes")
        run_button = gr.Button("Run", variant="primary")
        report = gr.Markdown(label="Report")
        
        run_button.click(fn=run, inputs=[query_textbox, to_emails], outputs=report)
        query_textbox.submit(fn=run, inputs=[query_textbox,to_emails], outputs=report)

    ui.launch(inbrowser=True)


