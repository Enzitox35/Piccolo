import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Sistema Piccolo", page_icon="👴", layout="wide")

# Menú Lateral
st.sidebar.title("Navegación")
opcion = st.sidebar.radio("Ir a:", ["Inicio", "Recordatorios", "Contactos", "Configuración"])

if opcion == "Inicio":
    st.title("☀️ ¡Buen día!")
    st.write("Bienvenido al **Sistema Piccolo**. ¿En qué puedo ayudarte hoy?")
    # Aquí puedes poner la imagen que mencionamos antes
    st.image("https://via.placeholder.com/600x300.png?text=Imagen+Bienvenida+Piccolo", caption="Asistente para Adultos Mayores")

elif opcion == "Recordatorios":
    st.title("📅 Mis Recordatorios")
    st.write("Aquí verás tus medicamentos y turnos médicos.")
    # Próximamente: Conexión a SQLite

elif opcion == "Contactos":
    st.title("📞 Contactos de Emergencia")
    st.write("Listado de personas a las que puedes llamar rápidamente.")