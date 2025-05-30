# Conversor DICOM

## Sobre o Projeto
Este aplicativo permite converter arquivos PDF ou imagens (PNG, JPG, BMP, TIFF) em arquivos DICOM, mantendo os metadados de um arquivo DICOM de origem. O DICOM (Digital Imaging and Communications in Medicine) é o padrão internacional para imagens médicas e informações relacionadas.

Desenvolvido por Julio Cesar Nather Junior.

## Funcionalidades

- Conversão de arquivos PDF em um ou mais arquivos DICOM
- Conversão de imagens (PNG, JPG, BMP, TIFF) em arquivos DICOM
- Preservação dos metadados relevantes do DICOM de origem
- Interface gráfica intuitiva em português
- Feedback visual durante o processo de conversão
- Salvamento automático na mesma pasta do arquivo de origem

## Requisitos do Sistema

- Python 3.6 ou superior
- Bibliotecas Python (instaladas automaticamente via requirements.txt):
  - pydicom: manipulação de arquivos DICOM
  - Pillow: processamento de imagens
  - pdf2image: conversão de PDF para imagens
- Para a conversão de PDF, é necessário o Poppler:
  - Windows: https://github.com/oschwartz10612/poppler-windows/releases/
  - Linux: `sudo apt-get install poppler-utils`
  - macOS: `brew install poppler`

## Instalação

1. Clone ou baixe este repositório.

2. Instale as dependências necessárias:
```
pip install -r requirements.txt
```

3. Instale o Poppler (necessário para conversão de PDF):
   - **Windows**: 
     - Baixe e extraia o Poppler de https://github.com/oschwartz10612/poppler-windows/releases/
     - Adicione a pasta `bin` ao PATH do sistema
   - **Linux**: 
     - `sudo apt-get install poppler-utils`
   - **macOS**: 
     - `brew install poppler`

## Como Usar

1. Execute o programa:
```
python main.py
```

2. Na interface do aplicativo:

   a. **Selecione o arquivo DICOM de origem**: 
      - Clique em "Procurar..." para selecionar um arquivo DICOM existente
      - Este arquivo servirá como modelo para os metadados do novo DICOM
      - As informações do paciente, estudo e outras serão extraídas automaticamente
   
   b. **Selecione o arquivo para converter**: 
      - Clique em "Procurar..." para selecionar um arquivo PDF ou imagem
      - Formatos suportados: PDF, PNG, JPG, JPEG, BMP, TIFF
      - Se selecionar um PDF com múltiplas páginas, cada página será convertida em um arquivo DICOM separado
   
   c. **Converter**: 
      - Clique no botão "Converter e Salvar Nova Série DICOM"
      - Os arquivos DICOM serão salvos na mesma pasta do arquivo de origem
      - Uma mensagem de sucesso será exibida quando a conversão for concluída

## Detalhes Técnicos

### Estrutura do Código

- **Interface Gráfica**: Construída usando Tkinter, a biblioteca padrão de GUI do Python
- **Processamento de Imagem**: Usa a biblioteca Pillow para manipulação de imagens
- **Manipulação DICOM**: Usa a biblioteca pydicom para ler/escrever arquivos DICOM
- **Conversão PDF**: Usa pdf2image (baseado em Poppler) para converter PDFs em imagens

### Metadados DICOM

O aplicativo preserva os seguintes metadados do arquivo DICOM de origem:
- StudyInstanceUID
- PatientName
- PatientID
- StudyDate
- StudyDescription
- Outros tags relevantes de identificação do paciente e estudo

Novos UIDs são gerados para:
- SeriesInstanceUID
- SOPInstanceUID

### Formato de Saída

Os arquivos DICOM gerados seguem o padrão:
```
SC_{SeriesUID curto}_{Número da instância}.dcm
```

Exemplo: `SC_12345678_001.dcm`

## Solução de Problemas

- **Erro ao converter PDF**: Verifique se o Poppler está instalado corretamente e no PATH do sistema.
- **Erro de arquivo não encontrado**: Verifique se os caminhos dos arquivos estão corretos.
- **DICOM inválido**: Verifique se o arquivo DICOM de origem é válido e não está corrompido.

## Limitações

- A conversão de imagens coloridas resulta em arquivos DICOM RGB
- A conversão de imagens em escala de cinza resulta em arquivos DICOM MONOCHROME2
- PDFs com elementos complexos podem não ser convertidos com alta fidelidade

## Licença

Este projeto é distribuído sob a licença MIT.
