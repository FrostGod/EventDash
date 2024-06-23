import json
import re
import os
import requests

from langchain import hub
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import JSONAgentOutputParser
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import StructuredTool, Tool
from langchain.tools.render import render_text_description_and_args
from langchain_community.tools.you import YouSearchTool
from langchain_community.utilities.you import YouSearchAPIWrapper

REACT_MULTI_JSON_PROMPT = hub.pull("hwchase17/react-multi-input-json")


class ChainInputSchema(BaseModel):
    input: str | None = Field(
        ...,
        description="Complete instruction to run the you.com agent.",
    )


class YouAgent:
    """
    Agent that uses the You API to search for only venue information, only for venue listings, 
    other contact information should be handled by other agents.
    """

    def __init__(self, llm, st, num_results) -> None:
        self.llm = llm
        self.st = st
        self.num_results = num_results
        self.chain = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_log_to_str(
                    x["intermediate_steps"],
                ),
            }
            | self.prompt
            | self.llm.bind(stop=["Observation"])
            | JSONAgentOutputParser()
        )

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def description(self) -> str:
        return self.__doc__

    @property
    def tools(self):
        os.environ["YDC_API_KEY"] = os.getenv("YOUAPIKEY")
        you_tool = YouSearchTool(
            api_wrapper=YouSearchAPIWrapper(num_web_results=3))
        return [
            you_tool
        ]

    @property
    def prompt(self):
        partial_prompt = REACT_MULTI_JSON_PROMPT.partial(
            tools=render_text_description_and_args(self.tools),
            tool_names=", ".join([t.name for t in self.tools]),
        )
        partial_prompt.messages[0].prompt.template = (
            re.sub(
                r"\s+",
                " ",
                f"""You are a helpful assistant called {self.name} able to call and
                orchestrate you.com agents to search for information. Provide accurate


                IMPORTANT:
                For each service, provide the following details in JSON format:
                - name: string
                - address: string
                - rating: float (1-5 stars)
                - phone: string
                - website: string
                - email: string
                - images: array of strings (up to 2 image URLs)

                Return the top {self.num_results} results as a list of JSON objects.
                If certain information is not available, use null for that field.
                """,
            )
            + partial_prompt.messages[0].prompt.template
        )
        return partial_prompt

    def as_executor(
        self,
        verbose=True,
        return_intermediate_steps=False,
        max_iterations=5,
        handle_parsing_errors=True,
        **kwargs,
    ) -> AgentExecutor:
        return AgentExecutor(
            agent=self.chain,
            tools=self.tools,
            verbose=verbose,
            return_intermediate_steps=return_intermediate_steps,
            max_iterations=max_iterations,
            handle_parsing_errors=handle_parsing_errors,
            **kwargs,
        )

    def get_random_venue_image(self):
        api_key = os.getenv("UNSPLASH_API_KEY")
        response = requests.get(
            f"https://api.unsplash.com/photos/random?query=event+venue&client_id={api_key}")
        if response.status_code == 200:
            return response.json()['urls']['regular']
        return "https: //whova.com/wp-content/uploads/2015/06/choose-perfect-event-venue.jpg"

    def get_carbon_footprint(self, venue):
        try:
            output = self.llm.invoke(
                f"""Estimate the carbon footprint of {venue} based on distance to Berkeley, display it as a rating. You should give an answer no matter what to your best knowledge
                Provide a super short explanation and super short number
                For example: 3.5 🍀, Reason: from Berkeley to SJ usually ...
                """
            ).content

            return output
        except:
            return "N/A"

    def show_venues(self, venues):
        st = self.st

        for venue in venues:
            st.header(venue.get('name', ''))
            col1, col2 = st.columns([1, 3])

            with col1:
                # Display the first image (or a placeholder if images are not available)
                # if venue['images']:
                #    st.image(venue['images'][0], width=150)
                # else:
                # st.image(self.get_random_venue_image(venue.get('name', ''))
                #         | "https://via.placeholder.com/150", width=150)
                st.image(self.get_random_venue_image(), width=150)

            with col2:
                st.markdown(
                    f"**Carbon Footprint:** {self.get_carbon_footprint(venue.get('name', ''))} 🍀")
                st.markdown(f"**Address:** {venue.get('address', '')}")
                st.markdown(f"**Rating:** {venue.get('rating', '')} ⭐")
                st.markdown(f"**Phone:** {venue.get('phone', '')}")
                st.markdown(
                    f"**Website:** [{venue.get('website', '')}]({venue.get('website', '')})")
                st.markdown(f"**Email:** {venue.get('email','')}")

                # if len(venue['images']) > 1:
                #    with st.expander("More images"):
                #        for image in venue['images'][1:]:
                #            st.image(image, width=150)

    def as_tool(
        self,
        return_direct=False,
        agent_kwargs={},
        tool_kwargs={},
    ) -> Tool:
        def run(input: str):
            res = self.as_executor(**agent_kwargs).invoke(
                {
                    "input": input,
                },
            )
            venues = res.get('output', [])
            self.show_venues(venues)

            return "Venues displayed successfully." + json.dumps(v.get('name', '') for v in venues)

        return StructuredTool.from_function(
            func=run,
            name=self.name,
            description=self.description,
            return_direct=return_direct,
            args_schema=ChainInputSchema,
            **tool_kwargs,
        )  # type: ignore
