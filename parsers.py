from Invoice import Invoice
from utils import date_parser, datetime_parser, date_to_str, quote


def parser_0(document):
    invoice_list = list()
    metadata = dict()
    metadata["communication_date"] = date_to_str(date_parser(document.attrib["Date"]))
    for item in document:
        if not item.tag.endswith("}Invoice"):
            continue
        invoice = Invoice()
        invoice.header["suppliers_document_number"] = quote(item.find("InvoiceReferences").find("SuppliersInvoiceNumber").text)
        invoice.header["document_number_full"] = invoice.header["suppliers_document_number"]
        invoice.header["issue_date"] = date_to_str(date_parser(item.find("InvoiceDate").text))
        invoice.header["issue_location"] = quote(item.find("CityOfIssue").text)
        invoice.header["sale_date"] = date_to_str(date_parser(item.find("TaxPointDate").text))
        invoice.header["receipt_date"] = invoice.header["sale_date"]
        invoice.header["order_id"] = quote(item.find("InvoiceReferences").find("BuyersOrderNumber").text) if item.find("InvoiceReferences").find("BuyersOrderNumber") else ""  # BuyersOrderNumber is sometimes absent in this XML schema
        invoice.header["currency"] = quote(item.find("InvoiceHead").find("InvoiceCurrency").find("Currency").attrib["Code"])
        # invoice.header[""] = quote(item.find("Supplier").find("SupplierReference").find("TaxNumber").text)  # Brak NIP sprzedawcy w EDI++
        # invoice.header["contractor_id"] = quote(item.find("Buyer").find("BuyerReferences").find("SuppliersCodeForBuyer").text)  # Prawidłowym źródłem jest Buyer.Party
        invoice.header["contractor_id"] = quote(item.find("Buyer").find("Party").text.replace(",", "")[:20])
        invoice.header["contractor_name_short"] = quote(item.find("Buyer").find("Party").text.replace(",", "")[:40])
        invoice.header["contractor_name_full"] = quote(item.find("Buyer").find("Party").text.replace(",", ""))
        invoice.header["contractor_tax_id"] = quote(item.find("Buyer").find("BuyerReferences").find("TaxNumber").text)
        invoice.header["contractor_address"] = quote(item.find("Buyer").find("Address").find("Street").text)
        invoice.header["contractor_city"] = quote(item.find("Buyer").find("Address").find("City").text)
        invoice.header["contractor_zip_code"] = quote(item.find("Buyer").find("Address").find("PostCode").text)
        invoice.header["payment_due"] = date_to_str(date_parser(item.find("Settlement").find("SettlementTerms").text))
        invoice.header["comment"] = quote(item.find("Narrative").text)
        invoice.header["remarks"] = quote(item.find("SpecialInstructions").text)
        if item.find("SpecialInstructions").text == "dokument liczony wg cen brutto":
            invoice.header["net_prices"] = False
            invoice.header["active_price"] = quote("brutto")
        invoice.header["number_of_entries"] = item.find("InvoiceTotal").find("NumberOfLines").text
        invoice.header["net_value"] = float(item.find("InvoiceTotal").find("LineValueTotal").text.replace(",", "."))
        invoice.header["vat_value"] = float(item.find("InvoiceTotal").find("TaxTotal").text.replace(",", "."))
        invoice.header["gross_value"] = float(item.find("InvoiceTotal").find("GrossPaymentTotal").text.replace(",", "."))
        invoice.header["amount_left_to_pay"] = invoice.header["gross_value"]
        for entry in item.findall("InvoiceLine"):
            invoice.body.append(
                {
                    # "tax_rate_symbol": entry.find("LineTax").find("TaxRate").attrib["Code"],  # Zastąpione rozwiązaniem wziętym z przykładu
                    "tax_rate_symbol": quote(entry.find("LineTax").find("TaxRate").text),
                    "tax_rate": float(entry.find("LineTax").find("TaxRate").text),
                    "net_value": round(float(entry.find("Price").find("UnitPrice").text.replace(",", ".")) * float(entry.find("Quantity").find("Amount").text.replace(",", ".")), 2),
                    "vat_value": float(entry.find("LineTax").find("TaxValue").text.replace(",", ".")),
                    "gross_value": float(entry.find("LineTotal").text.replace(",", "."))
                }
            )
        invoice_list.append(invoice)

    return metadata, invoice_list


def parser_1(document):
    invoice_list = []
    metadata = dict()
    metadata["communication_date"] = date_to_str(datetime_parser(document.attrib["date"]))
    for item in document:
        invoice = Invoice()
        invoice.header["document_type"] = quote("FS")
        invoice.header["suppliers_document_number"] = quote(item.find("inv_number_string").text)
        invoice.header["document_number_full"] = quote(item.find("inv_number_string").text)
        invoice.header["net_value"] = item.find("inv_price_net").text
        invoice.header["vat_value"] = item.find("inv_tax").text
        invoice.header["gross_value"] = item.find("inv_price").text
        invoice.header["amount_left_to_pay"] = item.find("inv_price").text
        invoice.header["issue_date"] = date_to_str(date_parser(item.find("inv_date").text))
        invoice.header["sale_date"] = date_to_str(date_parser(item.find("inv_sell_date").text))
        invoice.header["contractor_name_full"] = quote(item.find("inv_bill_company").text.replace(",", ""))
        invoice.header["contractor_name_short"] = quote(item.find("inv_bill_company").text.replace(",", "")[:40])
        invoice.header["contractor_id"] = quote(item.find("inv_bill_company").text.replace(",", "")[:20])
        invoice.header["contractor_tax_id"] = quote(item.find("inv_bill_vat").text) if item.find("inv_bill_vat").text else ''
        invoice.header["contractor_city"] = quote(item.find("inv_bill_city").text)
        invoice.header["contractor_country"] = quote(item.find("inv_bill_country").text)
        invoice.header["contractor_address"] = quote(item.find("inv_bill_street").text)
        invoice.header["contractor_zip_code"] = quote(item.find("inv_bill_code").text)
        invoice_list.append(invoice)
        invoice.body.append(
            {
                # "tax_rate_symbol": entry.find("LineTax").find("TaxRate").attrib["Code"],  # Zastąpione rozwiązaniem wziętym z przykładu
                "tax_rate_symbol": "\"23\"",
                "tax_rate": 23.0,
                "net_value": invoice.header["net_value"],
                "vat_value": invoice.header["vat_value"],
                "gross_value": invoice.header["gross_value"]
            }
        )
    return metadata, invoice_list
