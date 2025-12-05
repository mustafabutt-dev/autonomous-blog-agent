---
title: "Convert PPTX to PDF and JPG with Aspose.Slides for .NET"
seoTitle: "Convert PPTX to PDF and JPG with Aspose.Slides for .NET"
description: "Learn how to quickly convert PPTX files to PDF and JPG using Aspose.Slides for .NET with C# code examples and best practices."
date: Fri, 05 Dec 2025 13:08:14 +0000
lastmod: Fri, 05 Dec 2025 13:08:14 +0000
draft: false
url: /slides/convert-pptx-to-pdf-and-jpg-with-asposeslides-for-net/
author: "mushi"
summary: "This guide shows step by step how to convert PPTX presentations to PDF and JPG formats using Aspose.Slides for .NET in C#."
tags: ["Convert PPTX to PDF and JPG", "Convert PPT and PPTX to PDF in .NET", "Convert PPTX to PDF using C# | products.aspose.com", "Convert PPT and PPTX to JPG in .NET"]
categories: ["Aspose.Slides Product Family"]
showtoc: true
steps:
  - "Install Aspose.Slides for .NET via NuGet"
  - "Create a new C# console project"
  - "Load the PPTX file using Presentation class"
  - "Save the presentation as PDF"
  - "Save each slide as JPG image"
faqs:
  - q: "Can I convert PPTX to PDF without installing Microsoft Office?"
    a: "Yes, Aspose.Slides for .NET works independently of Microsoft Office. See the [documentation page](https://docs.aspose.com/slides/net/) for details."
  - q: "How can I control image quality when exporting to JPG?"
    a: "Use JpegOptions to set quality, compression level and resolution. Refer to the [API reference](https://reference.aspose.com/slides/net/) for full property list."
  - q: "Is it possible to convert multiple PPTX files in batch?"
    a: "Absolutely. You can loop through a folder of PPTX files and apply the same conversion logic. The free online app demonstrates batch conversion at [Aspose Slides App](https://products.aspose.app/slides)."
---

## Introduction

Converting PowerPoint presentations to PDF and image formats is a common requirement for sharing, archiving, and publishing content. With **Aspose.Slides for .NET**, developers can perform these conversions programmatically without relying on Microsoft Office. This article walks you through the complete process of converting a PPTX file to PDF and JPG using C#. You will also learn how to fine‑tune export options for optimal quality. For a deeper dive into the library’s capabilities, check out the official [product page](https://products.aspose.com/slides/net/).

## Steps to Convert PPTX to PDF and JPG

1. **Install Aspose.Slides for .NET via NuGet**:  
   Open the Package Manager Console and run the command below.  
   <!--[CODE_SNIPPET_START]-->
```powershell
Install-Package Aspose.Slides.NET
```
   <!--[CODE_SNIPPET_END]-->

2. **Create a new C# console project**:  
   Use Visual Studio or the `dotnet new console` command to set up a simple project where the conversion code will live.

3. **Load the PPTX file using Presentation class**:  
   The `Presentation` object reads the source file and gives access to slides, layouts and export settings.  
   <!--[CODE_SNIPPET_START]-->
```csharp
using Aspose.Slides;
using System;

var presentation = new Presentation("input.pptx");
```
   <!--[CODE_SNIPPET_END]-->

4. **Save the presentation as PDF**:  
   Call the `Save` method with `Export.SaveFormat.Pdf`. This step produces a high‑fidelity PDF version of the whole deck.

5. **Save each slide as JPG image**:  
   Iterate through the `Slides` collection and export each slide individually using `Export.SaveFormat.Jpeg`. You can also customize resolution and quality via `JpegOptions`.

## Setting up Aspose.Slides in a C# Project

Before writing conversion code, ensure that the Aspose.Slides assembly is referenced correctly. After installing the NuGet package, the required DLLs are added automatically. You may also need a temporary license for full functionality; obtain one from the [temporary license page](https://purchase.aspose.com/temporary-license/).

## Loading a PPTX Presentation

The `Presentation` class supports various input sources, including file paths, streams, and byte arrays. For large files, consider loading from a `FileStream` with `FileMode.Open` to reduce memory overhead.

```csharp
using (var stream = File.OpenRead("input.pptx"))
{
    var presentation = new Presentation(stream);
    // Continue with conversion...
}
```

## Exporting to PDF

Aspose.Slides preserves vector graphics, fonts and animations when exporting to PDF. You can adjust PDF export options such as compliance level, embed fonts, and document title via `PdfOptions`.

```csharp
var pdfOptions = new Aspose.Slides.Export.PdfOptions
{
    Compliance = Aspose.Slides.Export.PdfCompliance.PdfA2b,
    EmbedFullFonts = true
};
presentation.Save("output.pdf", Aspose.Slides.Export.SaveFormat.Pdf, pdfOptions);
```

## Exporting to JPG

When converting slides to images, you may need to specify the desired resolution and quality. `JpegOptions` lets you set `Quality` (0‑100) and `SourceRect` for cropping.

```csharp
var jpegOptions = new Aspose.Slides.Export.JpegOptions
{
    Quality = 90,
    Width = 1280,
    Height = 720
};

for (int i = 0; i < presentation.Slides.Count; i++)
{
    string imagePath = $"slide_{i + 1}.jpg";
    presentation.Slides[i].GetThumbnail(jpegOptions.Width, jpegOptions.Height).Save(imagePath, jpegOptions);
}
```

## Convert PPTX to PDF - Complete Code Example

The following console application demonstrates a full end‑to‑end conversion of a PPTX file to PDF. It includes error handling and uses the recommended `PdfOptions` for best results.

<!--[COMPLETE_CODE_SNIPPET_START]-->
{{< gist "mustafabutt" "ef6869ae2d83b6ee230a6a25bae3f3d6" "introduction_converting_powerpoint_presentations_t.csharp" >}}
<!--[COMPLETE_CODE_SNIPPET_END]-->

Run the program with the input PPTX file path and desired PDF output path as arguments.

## Convert PPTX to JPG - Complete Code Example

This example extracts each slide from a PPTX file and saves it as a high‑resolution JPG image. It demonstrates how to configure `JpegOptions` for quality and size.

<!--[COMPLETE_CODE_SNIPPET_START]-->
{{< gist "mustafabutt" "ef6869ae2d83b6ee230a6a25bae3f3d6" "convert_pptx_to_jpg.csharp" >}}
<!--[COMPLETE_CODE_SNIPPET_END]-->

Execute the program with the source PPTX file and a target folder where the JPG images will be stored.

## Conclusion

Aspose.Slides for .NET provides a powerful, Office‑independent way to convert PPTX presentations to both PDF and JPG formats. By following the steps and code samples above, you can integrate these conversions into any C# application, whether it’s a desktop tool, a web service, or a batch processing pipeline. For more advanced scenarios such as preserving hyperlinks, handling custom fonts, or converting to other image types, explore the extensive [API reference](https://reference.aspose.com/slides/net/) and the official blog posts in the [Aspose Slides product family](https://blog.aspose.com/categories/aspose.slides-product-family/).

## FAQs

**Q: Can I convert PPTX to PDF on a Linux server?**  
A: Yes, Aspose.Slides for .NET is cross‑platform and runs on .NET Core. No Microsoft Office installation is required. See the [documentation page](https://docs.aspose.com/slides/net/) for platform support details.

**Q: How do I set the DPI for JPG output?**  
A: Use the `Width` and `Height` properties of `JpegOptions` to control pixel dimensions, which effectively sets the DPI based on the slide size. Detailed property descriptions are available in the [API reference](https://reference.aspose.com/slides/net/).

**Q: Is there a way to convert PPTX files in bulk without writing custom code?**  
A: The free online tool at [Aspose Slides App](https://products.aspose.app/slides) supports batch uploads and converts multiple presentations to PDF or JPG in one click.

## Read More
- [Convert PPTX to XML in C# Programmatically](https://blog.aspose.com/slides/convert-pptx-to-xml-in-csharp/)
- [Convert PPTX to Markdown in C# using Aspose.Slides for .NET](https://blog.aspose.com/slides/pptx-to-markdown-in-csharp/)
- [PowerPoint Presentation Converter - Convert PPTX to EMF in C#](https://blog.aspose.com/slides/convert-pptx-to-emf-in-csharp/)