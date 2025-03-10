from dataclasses import dataclass
from typing import Literal
from urllib.parse import parse_qs, urlparse

from .errors import NoPositiveIntegerValue, UnsupportedFormat
from .filter_parser import FilterNode, ODataFilterParser


@dataclass
class ODataQueryOptions:
    count: bool = False
    expand: list[str] | None = None
    filter_: FilterNode | None = None
    format_: Literal['json', 'xml', 'csv', 'tsv'] | None = None
    orderby: list[dict[str, str]] | None = None
    search: str | None = None
    select: list[str] | None = None
    skip: int | None = None
    top: int | None = None


class ODataQueryParser:
    """Parser for OData V4 query options supporting
    standard query parameters.
    """

    def __init__(self):
        self.supported_options = {
            '$count': self._parse_count,
            '$expand': self._parse_expand,
            '$filter': self._parse_filter,
            '$format': self._parse_format,
            '$orderby': self._parse_orderby,
            '$search': self._parse_search,
            '$select': self._parse_select,
            '$skip': self._parse_skip,
            '$top': self._parse_top,
        }
        self.filter_parser = ODataFilterParser()

    def parse_url(self, url: str) -> ODataQueryOptions:
        """Parses a complete OData URL and
        extracts query options.

        Parameters
        ----------
        url : str
            Complete OData URL including query parameters.

        Returns
        -------
        ODataQueryOptions
            Parsed parameters.
        """
        parsed_url = urlparse(url)
        return self.parse_query_string(parsed_url.query)

    def parse_query_string(self, query_string: str) -> ODataQueryOptions:
        """Parses a complete OData query string and
        extracts query options.

        Parameters
        ----------
        query_string : str
            Complete OData query string including query parameters.

        Returns
        -------
        ODataQueryOptions
            Parsed parameters.
        """
        query_params = parse_qs(query_string)
        return self.parse_query_params(query_params)

    def parse_query_params(
        self, query_params: dict[str, list[str]]
    ) -> ODataQueryOptions:
        """Parses OData query parameters and
        returns structured options.

        Parameters
        ----------
        query_params : dict[str, list[str]]
            Dictionary of query parameters.

        Returns
        -------
        ODataQueryOptions
            Parsed parameters.
        """
        options = ODataQueryOptions()

        for param, values in query_params.items():
            if param in self.supported_options:
                # get the first value since OData parameters shouldn't
                # have multiple values
                value = values[0] if values else None
                if value is None:
                    continue

                parser_func = self.supported_options[param]
                parser_func(value, options)

        return options

    def _parse_count(self, value: str, options: ODataQueryOptions) -> None:
        """Parses $count parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.
        """
        options.count = value.lower() == 'true'

    def _parse_expand(self, value: str, options: ODataQueryOptions) -> None:
        """Parses $expand parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.
        """
        if value:
            options.expand = [item.strip() for item in value.split(',')]

    def _parse_filter(self, value: str, options: ODataQueryOptions) -> None:
        """Parses $filter parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.
        """
        options.filter_ = self.filter_parser.parse(value)

    def _parse_format(self, value: str, options: ODataQueryOptions) -> None:
        """Parses $format parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.

        Raises
        ------
        UnsupportedFormat
            If the format is not supported.
        """
        if value not in ('json', 'xml', 'csv', 'tsv'):
            raise UnsupportedFormat(value)

        options.format_ = value

    def _parse_orderby(self, value: str, options: ODataQueryOptions) -> None:
        """Parses $orderby parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.
        """
        if not value:
            return None

        orderby_list = []
        for item in value.split(','):
            item = item.strip()
            lowercased_item = item.lower()
            if lowercased_item.endswith(' asc'):
                field = item.replace(' asc', '').strip()
                direction = 'asc'
            elif lowercased_item.endswith(' desc'):
                field = item.replace(' desc', '').strip()
                direction = 'desc'
            else:
                field = item
                direction = 'asc'  # default direction

            orderby_list.append({'field': field, 'direction': direction})

        options.orderby = orderby_list

    def _parse_search(self, value: str, options: ODataQueryOptions) -> None:
        """Parses $search parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.
        """
        options.search = value.strip()

    def _parse_select(self, value: str, options: ODataQueryOptions) -> None:
        """Parses $select parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.
        """
        if value:
            options.select = [item.strip() for item in value.split(',')]

    def _parse_skip(self, value: str, options: ODataQueryOptions) -> None:
        """Parses $skip parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.

        Raises
        ------
        NoPositiveIntegerValue
            If the value is not a positive integer.
        """
        try:
            options.skip = int(value)
            assert options.skip >= 0
        except (AssertionError, ValueError, TypeError):
            raise NoPositiveIntegerValue('$skip', value)

    def _parse_top(self, value: str, options: ODataQueryOptions) -> None:
        """Parses $top parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.

        Raises
        ------
        NoPositiveIntegerValue
            If the value is not a positive integer.
        """
        try:
            options.top = int(value)
            assert options.top >= 0
        except (AssertionError, ValueError, TypeError):
            raise NoPositiveIntegerValue('$top', value)
