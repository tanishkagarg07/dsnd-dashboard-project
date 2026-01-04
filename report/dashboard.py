from fasthtml.common import *
import matplotlib.pyplot as plt

# Import QueryBase, Employee, Team from employee_events
from employee_events import QueryBase, Employee, Team

# import the load_model function from the utils.py file
from utils import load_model

"""
Below, we import the parent classes
you will use for subclassing
"""
from base_components import (
    Dropdown,
    BaseComponent,
    Radio,
    MatplotlibViz,
    DataTable
)

from combined_components import FormGroup, CombinedComponent


# Create a subclass of base_components/dropdown
# called `ReportDropdown`
class ReportDropdown(Dropdown):
    
    # Overwrite the build_component method
    # ensuring it has the same parameters
    # as the Report parent class's method
    def build_component(self, entity_id, model):
        #  Set the `label` attribute so it is set
        #  to the `name` attribute for the model
        self.label = model.name.capitalize()
        
        # Return the output from the
        # parent class's build_component method
        return super().build_component(entity_id, model)
    
    # Overwrite the `component_data` method
    # Ensure the method uses the same parameters
    # as the parent class method
    def component_data(self, entity_id, model):
        # Using the model argument
        # call the employee_events method
        # that returns the user-type's
        # names and ids
        return model.names()


# Create a subclass of base_components/BaseComponent
# called `Header`
class Header(BaseComponent):

    # Overwrite the `build_component` method
    # Ensure the method has the same parameters
    # as the parent class
    def build_component(self, entity_id, model):
        
        # Using the model argument for this method
        # return a fasthtml H1 objects
        # containing the model's name attribute
        return H1(f"{model.name.capitalize()} Report")


# Create a subclass of base_components/MatplotlibViz
# called `LineChart`
class LineChart(MatplotlibViz):
    
    # Overwrite the parent class's `visualization`
    # method. Use the same parameters as the parent
    def visualization(self, asset_id, model):

        # Pass the `asset_id` argument to
        # the model's `event_counts` method
        df = model.event_counts(asset_id)
        
        # Use the pandas .fillna method to fill nulls with 0
        df = df.fillna(0)
        
        # User the pandas .set_index method
        df = df.set_index('event_date')
        
        # Sort the index
        df = df.sort_index()
        
        # Use the .cumsum method
        df = df.cumsum()
        
        # Set the dataframe columns
        df.columns = ['Positive', 'Negative']
        
        # Initialize a pandas subplot
        fig, ax = plt.subplots()
        
        # Plot the cumulative counts
        df.plot(ax=ax)
        
        # Apply axis styling
        self.set_axis_styling(
            ax,
            border_color='black',
            font_color='black'
        )
        
        # Set title and labels
        ax.set_title('Cumulative Events')
        ax.set_xlabel('Date')
        ax.set_ylabel('Count')

        return fig


# Create a subclass of base_components/MatplotlibViz
# called `BarChart`
class BarChart(MatplotlibViz):

    # Create a `predictor` class attribute
    predictor = load_model()

    # Overwrite the parent class `visualization` method
    def visualization(self, asset_id, model):

        # Get model data
        data = model.model_data(asset_id)
        
        # Predict probabilities
        probs = self.predictor.predict_proba(data)
        
        # Take second column
        probs = probs[:, 1]
        
        # Determine prediction value
        if model.name == "team":
            pred = probs.mean()
        else:
            pred = probs[0]
        
        # Initialize plot
        fig, ax = plt.subplots()
        
        ax.barh([''], [pred])
        ax.set_xlim(0, 1)
        ax.set_title('Predicted Recruitment Risk', fontsize=20)
        
        # Apply axis styling
        self.set_axis_styling(
            ax,
            border_color='black',
            font_color='black'
        )

        return fig


# Create a subclass of combined_components/CombinedComponent
# called Visualizations       
class Visualizations(CombinedComponent):

    # Set the `children`
    children = [
        LineChart(),
        BarChart()
    ]

    # Leave this line unchanged
    outer_div_type = Div(cls='grid')


# Create a subclass of base_components/DataTable
# called `NotesTable`
class NotesTable(DataTable):

    # Overwrite the `component_data` method
    def component_data(self, entity_id, model):
        return model.notes(entity_id)


class DashboardFilters(FormGroup):

    id = "top-filters"
    action = "/update_data"
    method = "POST"

    children = [
        Radio(
            values=["Employee", "Team"],
            name='profile_type',
            hx_get='/update_dropdown',
            hx_target='#selector'
        ),
        ReportDropdown(
            id="selector",
            name="user-selection"
        )
    ]


# Create a subclass of CombinedComponents
# called `Report`
class Report(CombinedComponent):

    # Set the `children`
    children = [
        Header(),
        DashboardFilters(),
        Visualizations(),
        NotesTable()
    ]


# Initialize a fasthtml app 
app = FastHTML()

# Initialize the `Report` class
report = Report()


# Root route
@app.get('/')
def index():
    return report(1, Employee())


# Employee route
@app.get('/employee/{id}')
def employee(id: str):
    return report(int(id), Employee())


# Team route
@app.get('/team/{id}')
def team(id: str):
    return report(int(id), Team())


# Keep the below code unchanged!
@app.get('/update_dropdown{r}')
def update_dropdown(r):
    dropdown = DashboardFilters.children[1]
    print('PARAM', r.query_params['profile_type'])
    if r.query_params['profile_type'] == 'Team':
        return dropdown(None, Team())
    elif r.query_params['profile_type'] == 'Employee':
        return dropdown(None, Employee())


@app.post('/update_data')
async def update_data(r):
    from fasthtml.common import RedirectResponse
    data = await r.form()
    profile_type = data._dict['profile_type']
    id = data._dict['user-selection']
    if profile_type == 'Employee':
        return RedirectResponse(f"/employee/{id}", status_code=303)
    elif profile_type == 'Team':
        return RedirectResponse(f"/team/{id}", status_code=303)


serve()
