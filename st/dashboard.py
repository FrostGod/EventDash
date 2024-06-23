import matplotlib.pyplot as plt
from langchain.tools import StructuredTool
from langchain.pydantic_v1 import BaseModel, Field


class DashboardInput(BaseModel):
    """Input for the Dashboard tool."""
    query: str = Field(..., description="Query to generate the final budget")


class DashboardAgent:
    """
    Agent that creates and displays an event budget dashboard. called when user is satisfied
    """

    def __init__(self, llm, st):
        self.llm = llm
        self.st = st

    def create_event_budget_dashboard(self):
        # Sample budget data
        budget_data = {
            "Venue": 5000,
            "Catering": 3000,
            "Decorations": 1000,
            "Entertainment": 2000,
            "Miscellaneous": 1000
        }

        # Calculate total budget
        total_budget = sum(budget_data.values())

        # Create pie chart
        fig, ax = plt.subplots()
        ax.pie(budget_data.values(), labels=budget_data.keys(),
               autopct='%1.1f%%', startangle=90)
        ax.axis('equal')

        # Display the pie chart in Streamlit
        self.st.pyplot(fig)

        # Display total budget
        self.st.write(f"Total Budget: ${total_budget:,}")

        # Display budget breakdown
        self.st.write("Budget Breakdown:")
        for category, amount in budget_data.items():
            self.st.write(f"{category}: ${amount:,}")

        return "Dashboard created successfully."

    def as_tool(self) -> StructuredTool:
        """Convert the DashboardAgent to a StructuredTool."""
        return StructuredTool.from_function(
            func=self.run,
            name="DashboardTool",
            description="Creates and displays an event budget dashboard",
            args_schema=DashboardInput
        )

    def run(self, query: str) -> str:
        """Run the dashboard creation process."""
        self.st.title("Event Budget Dashboard")
        return self.create_event_budget_dashboard()
