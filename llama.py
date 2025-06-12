import streamlit as st
import replicate
import os

# App title
def run_llama_chat():

    st.markdown(
        f'<div class="title-container" style="margin-top: -60px; text-align: center;"><h2 style="color: navy; font-size: 40px;">R.e.s.i.M Chatbot</h2></div>',
        unsafe_allow_html=True)

    st.markdown(
        f'<div style="margin-top: -18px; text-align: center;"><h4 style="color: black;navy; font-size: 15px;">Response times may vary based on questions and parameters </h4></div>',
        unsafe_allow_html=True)

    # Description with increased font size
    st.markdown('<div class="big-font"> To use this chatbot  get a Free Replicate API token in 4 simple steps:</div>', unsafe_allow_html=True)

    st.markdown('<div class="big-font" style="margin-bottom: 10px;">1. Go to <a href="https://replicate.com/signin/" target="_blank">https://replicate.com/signin/</a>.</div>', unsafe_allow_html=True)
    st.markdown('<div class="big-font" style="margin-bottom: 10px;">2. Sign in with your GitHub account. <a href="https://github.com" target="_blank">https://github.com/</a>.</div>', unsafe_allow_html=True)
    st.markdown('<div class="big-font" style="margin-bottom: 10px;">3. Proceed to the API tokens page and copy your token.</div>', unsafe_allow_html=True)
    st.markdown('<div class="big-font" style="margin-bottom: 10px;">4. Paste the token in the input box and ask away!!.</div>', unsafe_allow_html=True)



    st.markdown(
        f'<div class="title-container" style="margin-top: 10px;"><h3 style="color: black;navy; font-size: 15px;">Settings:</h3></div>',
        unsafe_allow_html=True)

    def hint(text):
        return f"<span title='{text}'><span style='font-size: 16px; color: red; border-radius: 50%; border: 1px solid grey; padding: 0.5px 8px;'>?</span></span>"

    # CSS to style the custom components
    st.markdown("""
        <style>
            .big-font {
                font-size: 18px;
            }
        </style>
        """, unsafe_allow_html=True)

    st.markdown(
        f'<div class="title-container" style="margin-top: -20px;"><h2 style="color: navy; font-size: 25px;">Temperature </h2></div>',
        unsafe_allow_html=True)

    st.markdown('<div class="big-font" style="margin-bottom: 20px;">1. Controls the randomness of language model output. A higher setting causes the model to be more “confident” in its output. For example, if you adjust the level to 0.5, the model will generate text that is more predictable and less creative than if you set the temperature to 1.0.</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="title-container" style="margin-top: -20px;"><h2 style="color: navy; font-size: 25px;">Top_P</h2></div>',
        unsafe_allow_html=True)

    st.markdown('<div class="big-font" style="margin-bottom: 20px;">2. This is the number of words or characters in a sequence or text that is fed to the LLM. If it is set to 0.9, the model will only consider the most likely words that make up 90% of the probability mass.</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="title-container" style="margin-top: -20px;"><h2 style="color: navy; font-size: 25px;">Max Length</h2></div>',
        unsafe_allow_html=True)

    st.markdown('<div class="big-font" style="margin-bottom: 20px;">3. The length of the input text affects the output of the LLM. A very short input may not have enough context to generate a meaningful completion. Conversely, a rather long input may make the model inefficiently process or it may cause the model to generate an irrelevant output.</div>', unsafe_allow_html=True)


    # Replicate Credentials
    with st.sidebar:
        if 'REPLICATE_API_TOKEN' in st.secrets:
            st.success('API key already provided!', icon='✅')
            replicate_api = st.secrets['REPLICATE_API_TOKEN']
        else:
            replicate_api = st.text_input('Enter Replicate API token:', type='password')
            if not (replicate_api.startswith('r8_') and len(replicate_api) == 40):
                st.warning('Please enter your API Key!', icon='🔑')
            else:
                st.success('Success! Please ask your question below!', icon='➡️')

        # Refactored from https://github.com/a16z-infra/llama2-chatbot
        st.subheader('Models and parameters')
        selected_model = st.sidebar.selectbox('Choose a Llama2 model', ['Llama2-7B', 'Llama2-13B', 'Llama2-70B'], key='selected_model')
        if selected_model == 'Llama2-7B':
            llm = 'a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea'
        elif selected_model == 'Llama2-13B':
            llm = 'a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5'
        else:
            llm = 'replicate/llama70b-v2-chat:e951f18578850b652510200860fc4ea62b3b16fac280f83ff32282f87bbd2e48'

        temperature = st.sidebar.slider('temperature', min_value=0.01, max_value=5.0, value=0.1, step=0.01)
        top_p = st.sidebar.slider('top_p', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
        max_length = st.sidebar.slider('max_length', min_value=64, max_value=4096, value=512, step=8)


 

    os.environ['REPLICATE_API_TOKEN'] = replicate_api

    # Store LLM generated responses
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

    # Display or clear chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    def clear_chat_history():
        st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

    st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

    # Function for generating LLaMA2 response
    def generate_llama2_response(prompt_input):
        string_dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."
        for dict_message in st.session_state.messages:
            if dict_message["role"] == "user":
                string_dialogue += "User: " + dict_message["content"] + "\n\n"
            else:
                string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"
        output = replicate.run(llm,
                               input={"prompt": f"{string_dialogue} {prompt_input} Assistant: ",
                                      "temperature": temperature, "top_p": top_p, "max_length": max_length, "repetition_penalty": 1})
        return output

    # User-provided prompt
    if prompt := st.chat_input(disabled=not replicate_api):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

    # Generate a new response if the last message is not from the assistant
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = generate_llama2_response(prompt)
                placeholder = st.empty()
                full_response = ''
                for item in response:
                    full_response += item
                    placeholder.markdown(full_response)
                placeholder.markdown(full_response)
        message = {"role": "assistant", "content": full_response}
        st.session_state.messages.append(message)


