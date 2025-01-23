"""
This is useful as both a fastapi uvicorn server, AND as a library.

The API is OpenAI /v1/chat/completions compatible and works with litellm.

The API is stateful, in that it assumes:

* the server or working directory is located in a git repo
* it has access to read and update history files and make commits

So you DON'T need to pass more than one message to it each interaction.

How it differs from `aider.main:main` however is it is not a live session.
It will send you Y/N questions as responses, then "stops". Then resume when you send an answer back.
whereas `aider.main:main` maintains a live connection in your terminal and "hangs" until you reply.

I will call this distinction "transactional" vs "live"

So this is a "stateful" "transactional" api. Whereas the other is a "stateful" "live" environment.

Some term translation:

* assistant_id -> branch starting with aider/
* thread_id -> history file suffix (small hash) inside a threads/ folder
* message_id -> the counting integer of the message inside input-history-file

### To implement later
* run_id -> In the history file, example: # aider chat started at 2024-06-05 12:24:25
* step_id -> A counting integer starting at the run_id counting the > or ####

"""

from typing import ClassVar, List, Optional, Tuple

from pydantic import Field, StrictInt, StrictStr
from typing_extensions import Annotated

from aider.api.apis.assistants_api_base import BaseAssistantsApi
from aider.api.models.assistant_object import AssistantObject
from aider.api.models.create_assistant_request import CreateAssistantRequest
from aider.api.models.create_message_request import CreateMessageRequest
from aider.api.models.create_run_request import CreateRunRequest
from aider.api.models.create_thread_and_run_request import CreateThreadAndRunRequest
from aider.api.models.create_thread_request import CreateThreadRequest
from aider.api.models.delete_assistant_response import DeleteAssistantResponse
from aider.api.models.delete_message_response import DeleteMessageResponse
from aider.api.models.delete_thread_response import DeleteThreadResponse
from aider.api.models.list_assistants_response import ListAssistantsResponse
from aider.api.models.list_messages_response import ListMessagesResponse
from aider.api.models.list_run_steps_response import ListRunStepsResponse
from aider.api.models.list_runs_response import ListRunsResponse
from aider.api.models.message_object import MessageObject
from aider.api.models.modify_assistant_request import ModifyAssistantRequest
from aider.api.models.modify_message_request import ModifyMessageRequest
from aider.api.models.modify_run_request import ModifyRunRequest
from aider.api.models.modify_thread_request import ModifyThreadRequest
from aider.api.models.run_object import RunObject
from aider.api.models.run_step_object import RunStepObject
from aider.api.models.submit_tool_outputs_run_request import SubmitToolOutputsRunRequest
from aider.api.models.thread_object import ThreadObject


class AiderAssistantsApi(BaseAssistantsApi):
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseAssistantsApi.subclasses = BaseAssistantsApi.subclasses + (cls,)

    async def cancel_run(
        self,
        thread_id: Annotated[
            StrictStr, Field(description="The ID of the thread to which this run belongs.")
        ],
        run_id: Annotated[StrictStr, Field(description="The ID of the run to cancel.")],
    ) -> RunObject:
        """cancel_run is not supported"""
        raise NotImplementedError("WON'T DO")

    async def create_assistant(
        self,
        create_assistant_request: CreateAssistantRequest,
    ) -> AssistantObject:
        """Creates a branch and resets all the history files and tracks them"""
        raise NotImplementedError("TODO")

    async def create_message(
        self,
        thread_id: Annotated[
            StrictStr,
            Field(
                description="The ID of the [thread](/docs/api-reference/threads)"
                " to create a message for."
            ),
        ],
        create_message_request: CreateMessageRequest,
    ) -> MessageObject:
        """Add a user message to the history"""
        raise NotImplementedError("TODO")

    async def create_run(
        self,
        thread_id: Annotated[StrictStr, Field(description="The ID of the thread to run.")],
        create_run_request: CreateRunRequest,
        include: Annotated[
            Optional[List[StrictStr]],
            Field(
                description="A list of additional fields to include in the response."
                " Currently the only supported value is"
                " `step_details.tool_calls[*].file_search.results[*].content`"
                " to fetch the file search result content."
                "  See the [file search tool documentation]"
                "(/docs/assistants/tools/file-search#customizing-file-search-settings)"
                " for more information. "
            ),
        ],
    ) -> RunObject:
        """Run aider"""
        raise NotImplementedError("TODO")

    async def create_thread(
        self,
        create_thread_request: Optional[CreateThreadRequest],
    ) -> ThreadObject:
        """Creates a new set of history objects under the thread id and tracks them"""
        raise NotImplementedError("TODO")

    async def create_thread_and_run(
        self,
        create_thread_and_run_request: CreateThreadAndRunRequest,
    ) -> RunObject:
        thread_object = await self.create_thread(create_thread_and_run_request.thread)
        return await self.create_run(
            thread_id=thread_object.id,
            create_run_request=CreateRunRequest.from_dict(vars(create_thread_and_run_request)),
            include=None,
        )

    async def delete_assistant(
        self,
        assistant_id: Annotated[StrictStr, Field(description="The ID of the assistant to delete.")],
    ) -> DeleteAssistantResponse:
        """Deletes the branch called assistant_id"""
        raise NotImplementedError("TODO")

    async def delete_message(
        self,
        thread_id: Annotated[
            StrictStr, Field(description="The ID of the thread to which this message belongs.")
        ],
        message_id: Annotated[StrictStr, Field(description="The ID of the message to delete.")],
    ) -> DeleteMessageResponse:
        """Deletes the message from the history files"""
        raise NotImplementedError("LATER")

    async def delete_thread(
        self,
        thread_id: Annotated[StrictStr, Field(description="The ID of the thread to delete.")],
    ) -> DeleteThreadResponse:
        """Deletes the history files"""
        raise NotImplementedError("TODO")

    async def get_assistant(
        self,
        assistant_id: Annotated[
            StrictStr, Field(description="The ID of the assistant to retrieve.")
        ],
    ) -> AssistantObject:
        """Get some info about the branch"""
        raise NotImplementedError("LATER")

    async def get_message(
        self,
        thread_id: Annotated[
            StrictStr,
            Field(
                description="The ID of the [thread](/docs/api-reference/threads)"
                " to which this message belongs."
            ),
        ],
        message_id: Annotated[StrictStr, Field(description="The ID of the message to retrieve.")],
    ) -> MessageObject:
        raise NotImplementedError("LATER")

    async def get_run(
        self,
        thread_id: Annotated[
            StrictStr,
            Field(description="The ID of the [thread](/docs/api-reference/threads) that was run."),
        ],
        run_id: Annotated[StrictStr, Field(description="The ID of the run to retrieve.")],
    ) -> RunObject:
        raise NotImplementedError("LATER")

    async def get_run_step(
        self,
        thread_id: Annotated[
            StrictStr,
            Field(description="The ID of the thread to which the run and run step belongs."),
        ],
        run_id: Annotated[
            StrictStr, Field(description="The ID of the run to which the run step belongs.")
        ],
        step_id: Annotated[StrictStr, Field(description="The ID of the run step to retrieve.")],
        include: Annotated[
            Optional[List[StrictStr]],
            Field(
                description="A list of additional fields to include in the response."
                " Currently the only supported value is"
                " `step_details.tool_calls[*].file_search.results[*].content` to fetch the file"
                "search result content."
                " See the [file search tool documentation]"
                "(/docs/assistants/tools/file-search#customizing-file-search-settings)"
                " for more information. "
            ),
        ],
    ) -> RunStepObject:
        raise NotImplementedError("LATER")

    async def get_thread(
        self,
        thread_id: Annotated[StrictStr, Field(description="The ID of the thread to retrieve.")],
    ) -> ThreadObject:
        """Just returns the history file"""
        raise NotImplementedError("TODO")

    async def list_assistants(
        self,
        limit: Annotated[
            Optional[StrictInt],
            Field(
                description="A limit on the number of objects to be returned. Limit can range"
                " between 1 and 100, and the default is 20. "
            ),
        ],
        order: Annotated[
            Optional[StrictStr],
            Field(
                description="Sort order by the `created_at` timestamp of the objects. `asc` for"
                " ascending order and `desc` for descending order. "
            ),
        ],
        after: Annotated[
            Optional[StrictStr],
            Field(
                description="A cursor for use in pagination. `after` is an object ID that"
                " defines your place in the list. For instance, if you make a list request and"
                " receive 100 objects, ending with obj_foo, your subsequent call can"
                " include after=obj_foo in order to fetch the next page of the list. "
            ),
        ],
        before: Annotated[
            Optional[StrictStr],
            Field(
                description="A cursor for use in pagination. `before` is an object ID that"
                " defines your place in the list. For instance, if you make a list request"
                " and receive 100 objects, starting with obj_foo, your subsequent call"
                " can include before=obj_foo in order to fetch the previous page of the list."
            ),
        ],
    ) -> ListAssistantsResponse:
        """Just lists the aider/ branches"""
        raise NotImplementedError("TODO")

    async def list_messages(
        self,
        thread_id: Annotated[
            StrictStr,
            Field(
                description="The ID of the [thread](/docs/api-reference/threads)"
                " the messages belong to."
            ),
        ],
        limit: Annotated[
            Optional[StrictInt],
            Field(
                description="A limit on the number of objects to be returned."
                " Limit can range between 1 and 100, and the default is 20. "
            ),
        ],
        order: Annotated[
            Optional[StrictStr],
            Field(
                description="Sort order by the `created_at` timestamp of the objects."
                " `asc` for ascending order and `desc` for descending order. "
            ),
        ],
        after: Annotated[
            Optional[StrictStr],
            Field(
                description="A cursor for use in pagination. `after` is an object ID that"
                " defines your place in the list. For instance, if you make a list request"
                " and receive 100 objects, ending with obj_foo, your subsequent call can"
                " include after=obj_foo in order to fetch the next page of the list."
            ),
        ],
        before: Annotated[
            Optional[StrictStr],
            Field(
                description="A cursor for use in pagination. `before` is an object ID that"
                " defines your place in the list. For instance, if you make a list request"
                " and receive 100 objects, starting with obj_foo, your subsequent call can"
                " include before=obj_foo in order to fetch the previous page of the list. "
            ),
        ],
        run_id: Annotated[
            Optional[StrictStr],
            Field(description="Filter messages by the run ID that generated them. "),
        ],
    ) -> ListMessagesResponse:
        """Just returns the aider_input_history file. IGNORES run_id"""
        assert run_id is None, "run_id is not supported"
        raise NotImplementedError("LATER")

    async def list_run_steps(
        self,
        thread_id: Annotated[
            StrictStr, Field(description="The ID of the thread the run and run steps belong to.")
        ],
        run_id: Annotated[
            StrictStr, Field(description="The ID of the run the run steps belong to.")
        ],
        limit: Annotated[
            Optional[StrictInt],
            Field(
                description="A limit on the number of objects to be returned. Limit can range"
                " between 1 and 100, and the default is 20. "
            ),
        ],
        order: Annotated[
            Optional[StrictStr],
            Field(
                description="Sort order by the `created_at` timestamp of the objects."
                " `asc` for ascending order and `desc` for descending order. "
            ),
        ],
        after: Annotated[
            Optional[StrictStr],
            Field(
                description="A cursor for use in pagination. `after` is an object ID that"
                " defines your place in the list. For instance, if you make a list request"
                " and receive 100 objects, ending with obj_foo, your subsequent call can"
                " include after=obj_foo in order to fetch the next page of the list. "
            ),
        ],
        before: Annotated[
            Optional[StrictStr],
            Field(
                description="A cursor for use in pagination. `before` is an object ID"
                " that defines your place in the list. For instance, if you make a list"
                " request and receive 100 objects, starting with obj_foo, your subsequent"
                " call can include before=obj_foo in order to fetch the previous page of the list. "
            ),
        ],
        include: Annotated[
            Optional[List[StrictStr]],
            Field(
                description="A list of additional fields to include in the response."
                " Currently the only supported value is"
                " `step_details.tool_calls[*].file_search.results[*].content`"
                " to fetch the file search result content."
                "  See the "
                "[file search tool documentation]"
                "(/docs/assistants/tools/file-search#customizing-file-search-settings)"
                " for more information. "
            ),
        ],
    ) -> ListRunStepsResponse:
        """Just returns the aider_llm_history file"""
        raise NotImplementedError("LATER")

    async def list_runs(
        self,
        thread_id: Annotated[
            StrictStr, Field(description="The ID of the thread the run belongs to.")
        ],
        limit: Annotated[
            Optional[StrictInt],
            Field(
                description="A limit on the number of objects to be returned."
                " Limit can range between 1 and 100, and the default is 20. "
            ),
        ],
        order: Annotated[
            Optional[StrictStr],
            Field(
                description="Sort order by the `created_at` timestamp of the objects."
                " `asc` for ascending order and `desc` for descending order. "
            ),
        ],
        after: Annotated[
            Optional[StrictStr],
            Field(
                description="A cursor for use in pagination. `after` is an object ID"
                " that defines your place in the list. For instance, if you make a list"
                " request and receive 100 objects, ending with obj_foo, your subsequent"
                " call can include after=obj_foo in order to fetch the next page of the list. "
            ),
        ],
        before: Annotated[
            Optional[StrictStr],
            Field(
                description="A cursor for use in pagination. `before` is an object ID"
                " that defines your place in the list. For instance, if you make a list"
                " request and receive 100 objects, starting with obj_foo, your"
                " subsequent call can include before=obj_foo in order to fetch"
                " the previous page of the list. "
            ),
        ],
    ) -> ListRunsResponse:
        raise NotImplementedError("LATER")

    async def modify_assistant(
        self,
        assistant_id: Annotated[StrictStr, Field(description="The ID of the assistant to modify.")],
        modify_assistant_request: ModifyAssistantRequest,
    ) -> AssistantObject:
        """Too complicated, not necessary"""
        raise NotImplementedError("WON'T DO")

    async def modify_message(
        self,
        thread_id: Annotated[
            StrictStr, Field(description="The ID of the thread to which this message belongs.")
        ],
        message_id: Annotated[StrictStr, Field(description="The ID of the message to modify.")],
        modify_message_request: ModifyMessageRequest,
    ) -> MessageObject:
        raise NotImplementedError("LATER")

    async def modify_run(
        self,
        thread_id: Annotated[
            StrictStr,
            Field(description="The ID of the [thread](/docs/api-reference/threads) that was run."),
        ],
        run_id: Annotated[StrictStr, Field(description="The ID of the run to modify.")],
        modify_run_request: ModifyRunRequest,
    ) -> RunObject:
        raise NotImplementedError("WON'T DO")

    async def modify_thread(
        self,
        thread_id: Annotated[
            StrictStr,
            Field(
                description="The ID of the thread to modify. Only the `metadata` can be modified."
            ),
        ],
        modify_thread_request: ModifyThreadRequest,
    ) -> ThreadObject:
        raise NotImplementedError("LATER")

    async def submit_tool_ouputs_to_run(
        self,
        thread_id: Annotated[
            StrictStr,
            Field(
                description="The ID of the [thread](/docs/api-reference/threads)"
                " to which this run belongs."
            ),
        ],
        run_id: Annotated[
            StrictStr,
            Field(description="The ID of the run that requires the tool output submission."),
        ],
        submit_tool_outputs_run_request: SubmitToolOutputsRunRequest,
    ) -> RunObject:
        raise NotImplementedError("LATER")
